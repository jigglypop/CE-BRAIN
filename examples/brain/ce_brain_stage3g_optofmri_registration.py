"""Outcome-blind atlas-registration gate for CNIR opto-fMRI.

The sample gate uses only anatomy and an author-produced atlas registration.
No stimulation-response image is read.  SimpleITK is an optional runtime
dependency because the repository's ordinary tests exercise the pure audit
logic without performing medical-image registration.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from examples.brain.ce_brain_stage3f_optofmri_state_rdm import DEVELOPMENT, _download_one
from examples.brain.ce_brain_stage3f_optofmri_state_rdm import SITES


ASSET_SHA256 = {
    "Brain_template.nii": "7c255600e7eac3819e6c2ed761b5218cce0e7d6d13f80795ca59b449768b8b49",
    "Allen_annotation_modified.nii": "171f2c80a16247df413ed1927644993bb008c5e6a12de08a30e6735ffb80d409",
    "Atlas_anno_to_T2.nii": "11d89fbb18faa9afef754a59c5e51dbdaa013d9e7cd8e9a01398eafea11a37ea",
    "Atlas_T2_coreg.txt": "020238f7af7c58f677bc70fd7f1fef0fdacf9e9adeada79d9fe292ebe766f236",
    "sub01_struct_T2RARE.nii": "e25f50e168ba9b8ee262897d899c8877a224cbfd640d9683329327b273ecb8d0",
    "T2w_resample.nii": "6d34e3dbd7a206a13d6cfeeaaa62bcdee94a72e2b34ee98d6653f8a6149c8a88",
    "Readme.docx": "42b3549313609c2bd96b3fcf53448dbce170fcc25153fba3fdd22b9b1e97c4ba",
    "DMD_pattern_prep.m": "ca357e2d09cbd050e827260b8cbe88ea8685215f06a29cdf0d6bce0be590a8ce",
    "Load_ATLAS_info.m": "8ac97c5e2a4d26ffc029d85d7c90f99d5d4f4b9f645d0ced2e819f3b56ebdb9a",
    "DMD_pattern_generation.m": "6c3649599d8c17753e84dfbe3194a8f29aa8ddcb0637b707a45a25f4f52a8908",
}

# Base labels and the number of cortical layer labels folded into each base by
# the authors' DMD_pattern_prep.m.  Each family includes both hemispheres.
SOURCE_BASES = {
    "MOp": ((18, 5),),
    "MOs": ((24, 5),),
    "SSp-bfd": ((51, 6),),
    "VISp": ((185, 6),),
    "RSP": ((298, 5), (325, 6), (332, 6)),
    "VISarl": ((346, 6), (353, 6)),
}

FOREGROUND_DICE_MIN = 0.90
MEDIAN_SOURCE_DICE_MIN = 0.50
MIN_SOURCE_DICE_MIN = 0.35
ANATOMY_OTSU_DICE_MIN = 0.75
ANATOMY_METRIC_MAX = -0.30
AFFINE_DETERMINANT_RANGE = (0.80, 1.40)
EPI_OTSU_DICE_MIN = 0.75
EPI_METRIC_MAX = -0.50
EPI_AFFINE_DETERMINANT_RANGE = (0.80, 1.20)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_assets(asset_dir: Path) -> dict[str, object]:
    observed: dict[str, str] = {}
    mismatches: list[str] = []
    for name, expected in ASSET_SHA256.items():
        path = asset_dir / name
        if not path.is_file():
            mismatches.append(f"missing:{name}")
            continue
        observed[name] = sha256_file(path)
        if observed[name] != expected:
            mismatches.append(f"sha256:{name}")
    return {"ok": not mismatches, "mismatches": mismatches, "sha256": observed}


def select_development_anatomy_entries(
    manifest: list[dict[str, object]],
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for subject in (subject for cohort in DEVELOPMENT.values() for subject in cohort):
        expected = f"{subject}/anat/T2w.nii.gz"
        matches = [row for row in manifest if row["filename"] == expected]
        if len(matches) != 1:
            raise ValueError(f"expected one anatomy entry for {subject}, found {len(matches)}")
        selected.append(matches[0])
    return selected


def download_development_anatomy(
    manifest_path: Path,
    output_root: Path,
    workers: int = 4,
) -> list[dict[str, object]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = select_development_anatomy_entries(manifest)
    records: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_download_one, entry, output_root): entry for entry in entries}
        for index, future in enumerate(as_completed(futures), 1):
            record = future.result()
            records.append(record)
            print(f"[{index}/{len(entries)}] {record['filename']}", flush=True)
    return sorted(records, key=lambda row: str(row["filename"]))


def expanded_labels(bases: Iterable[tuple[int, int]]) -> tuple[int, ...]:
    labels: list[int] = []
    for base, layers in bases:
        for hemisphere_offset in (0, 2000):
            labels.extend(base + hemisphere_offset + layer for layer in range(layers + 1))
    return tuple(labels)


def dice(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=bool)
    right = np.asarray(right, dtype=bool)
    denominator = int(left.sum()) + int(right.sum())
    return 1.0 if denominator == 0 else 2.0 * int(np.logical_and(left, right).sum()) / denominator


def scaled_origin_preserving_center(
    size: Iterable[int],
    spacing: Iterable[float],
    origin: Iterable[float],
    direction: Iterable[float],
    factor: float,
) -> tuple[float, ...]:
    size_array = np.asarray(tuple(size), dtype=float)
    spacing_array = np.asarray(tuple(spacing), dtype=float)
    origin_array = np.asarray(tuple(origin), dtype=float)
    direction_matrix = np.asarray(tuple(direction), dtype=float).reshape(3, 3)
    half_index = 0.5 * (size_array - 1.0)
    center = origin_array + direction_matrix @ (half_index * spacing_array)
    new_offset = direction_matrix @ (half_index * spacing_array * factor)
    return tuple(float(value) for value in center - new_offset)


def scale_spacing_preserve_center(image: object, factor: float = 10.0) -> object:
    """Match the authors' AFNI ``3drefit -xyzscale 10`` geometry."""
    import SimpleITK as sitk

    scaled = sitk.Image(image)
    new_origin = scaled_origin_preserving_center(
        image.GetSize(), image.GetSpacing(), image.GetOrigin(), image.GetDirection(), factor
    )
    scaled.SetSpacing(tuple(float(value) * factor for value in image.GetSpacing()))
    scaled.SetOrigin(new_origin)
    return scaled


def label_dice(candidate: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    scores = {"foreground": dice(candidate > 0, reference > 0)}
    for name, bases in SOURCE_BASES.items():
        labels = expanded_labels(bases)
        scores[name] = dice(np.isin(candidate, labels), np.isin(reference, labels))
    return scores


def judge_sample(scores: dict[str, float]) -> dict[str, object]:
    source_scores = np.array([scores[name] for name in SOURCE_BASES], dtype=float)
    median_source = float(np.median(source_scores))
    minimum_source = float(np.min(source_scores))
    passed = (
        scores["foreground"] >= FOREGROUND_DICE_MIN
        and median_source >= MEDIAN_SOURCE_DICE_MIN
        and minimum_source >= MIN_SOURCE_DICE_MIN
    )
    return {
        "foreground_dice": float(scores["foreground"]),
        "source_dice": {name: float(scores[name]) for name in SOURCE_BASES},
        "median_source_dice": median_source,
        "minimum_source_dice": minimum_source,
        "thresholds": {
            "foreground_dice_min": FOREGROUND_DICE_MIN,
            "median_source_dice_min": MEDIAN_SOURCE_DICE_MIN,
            "minimum_source_dice_min": MIN_SOURCE_DICE_MIN,
        },
        "status": "SAMPLE_REGISTRATION_GATE_PASS" if passed else "SAMPLE_REGISTRATION_GATE_FAIL",
    }


def _run_rigid_registration(fixed: object, moving: object, seed: int) -> tuple[object, object]:
    import SimpleITK as sitk

    sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(1)
    initial = sitk.CenteredTransformInitializer(
        fixed,
        moving,
        sitk.Euler3DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY,
    )
    registration = sitk.ImageRegistrationMethod()
    registration.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration.SetMetricSamplingStrategy(registration.RANDOM)
    registration.SetMetricSamplingPercentage(0.10, seed=seed)
    registration.SetInterpolator(sitk.sitkLinear)
    registration.SetOptimizerAsRegularStepGradientDescent(
        learningRate=2.0,
        minStep=0.001,
        numberOfIterations=300,
        relaxationFactor=0.5,
    )
    registration.SetOptimizerScalesFromPhysicalShift()
    registration.SetShrinkFactorsPerLevel((4, 2, 1))
    registration.SetSmoothingSigmasPerLevel((2, 1, 0))
    registration.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    registration.SetInitialTransform(initial, inPlace=False)
    return registration.Execute(fixed, moving), registration


def _run_affine_registration(fixed: object, moving: object, seed: int) -> tuple[object, object]:
    import SimpleITK as sitk

    sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(1)
    rigid_composite, _ = _run_rigid_registration(fixed, moving, seed)
    rigid = sitk.Euler3DTransform(rigid_composite.GetBackTransform())
    affine = sitk.AffineTransform(3)
    affine.SetCenter(rigid.GetCenter())
    affine.SetMatrix(rigid.GetMatrix())
    affine.SetTranslation(rigid.GetTranslation())
    registration = sitk.ImageRegistrationMethod()
    registration.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration.SetMetricSamplingStrategy(registration.RANDOM)
    registration.SetMetricSamplingPercentage(0.15, seed=seed)
    registration.SetInterpolator(sitk.sitkLinear)
    registration.SetOptimizerAsRegularStepGradientDescent(
        learningRate=1.0,
        minStep=0.0001,
        numberOfIterations=500,
        relaxationFactor=0.5,
    )
    registration.SetOptimizerScalesFromPhysicalShift()
    registration.SetShrinkFactorsPerLevel((4, 2, 1))
    registration.SetSmoothingSigmasPerLevel((2, 1, 0))
    registration.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    registration.SetInitialTransform(affine, inPlace=False)
    return registration.Execute(fixed, moving), registration


def register_rigid_sample(asset_dir: Path, seed: int = 42) -> tuple[dict[str, object], object]:
    try:
        import SimpleITK as sitk
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError("SimpleITK is required only for the registration CLI") from error

    fixed = sitk.ReadImage(str(asset_dir / "T2w_resample.nii"), sitk.sitkFloat32)
    moving = sitk.ReadImage(str(asset_dir / "Brain_template.nii"), sitk.sitkFloat32)
    moving_labels = sitk.ReadImage(str(asset_dir / "Allen_annotation_modified.nii"))
    reference_labels = sitk.ReadImage(str(asset_dir / "Atlas_anno_to_T2.nii"))

    transform, registration = _run_rigid_registration(fixed, moving, seed)

    warped = sitk.Resample(
        moving_labels,
        reference_labels,
        transform,
        sitk.sitkNearestNeighbor,
        0,
        reference_labels.GetPixelID(),
    )
    candidate = sitk.GetArrayViewFromImage(warped)
    reference = sitk.GetArrayViewFromImage(reference_labels)
    scores = label_dice(candidate, reference)
    result = judge_sample(scores)
    result.update(
        {
            "algorithm": "deterministic-rigid-mattes-mi-v1",
            "seed": seed,
            "metric_value": float(registration.GetMetricValue()),
            "optimizer_stop": registration.GetOptimizerStopConditionDescription(),
            "outcome_data_used": False,
        }
    )
    return result, transform


def register_affine_sample(asset_dir: Path, seed: int = 42) -> tuple[dict[str, object], object]:
    """Refine the failed rigid candidate with an anatomy-only affine transform."""
    try:
        import SimpleITK as sitk
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError("SimpleITK is required only for the registration CLI") from error

    fixed = sitk.ReadImage(str(asset_dir / "T2w_resample.nii"), sitk.sitkFloat32)
    moving = sitk.ReadImage(str(asset_dir / "Brain_template.nii"), sitk.sitkFloat32)
    moving_labels = sitk.ReadImage(str(asset_dir / "Allen_annotation_modified.nii"))
    reference_labels = sitk.ReadImage(str(asset_dir / "Atlas_anno_to_T2.nii"))
    transform, registration = _run_affine_registration(fixed, moving, seed)
    warped = sitk.Resample(
        moving_labels,
        reference_labels,
        transform,
        sitk.sitkNearestNeighbor,
        0,
        reference_labels.GetPixelID(),
    )
    scores = label_dice(
        sitk.GetArrayViewFromImage(warped),
        sitk.GetArrayViewFromImage(reference_labels),
    )
    result = judge_sample(scores)
    result.update(
        {
            "algorithm": "rigid-plus-affine-mattes-mi-v1",
            "seed": seed,
            "metric_value": float(registration.GetMetricValue()),
            "optimizer_stop": registration.GetOptimizerStopConditionDescription(),
            "outcome_data_used": False,
        }
    )
    return result, transform


def register_development_anatomy(
    asset_dir: Path,
    development_root: Path,
    output_dir: Path,
    seed: int = 42,
) -> dict[str, object]:
    """Apply the locked anatomy-only registration to the 12 development animals."""
    try:
        import SimpleITK as sitk
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError("SimpleITK is required only for the registration CLI") from error

    moving = sitk.ReadImage(str(asset_dir / "Brain_template.nii"), sitk.sitkFloat32)
    moving_labels = sitk.ReadImage(str(asset_dir / "Allen_annotation_modified.nii"))
    moving_mask = sitk.OtsuThreshold(moving, 0, 1)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for subject in (subject for cohort in DEVELOPMENT.values() for subject in cohort):
        path = development_root / subject / "anat" / "T2w.nii.gz"
        raw = sitk.ReadImage(str(path), sitk.sitkFloat32)
        geometry_ok = raw.GetSize() == (160, 100, 120) and all(
            abs(value - 0.1) < 1e-5 for value in raw.GetSpacing()
        )
        fixed = scale_spacing_preserve_center(raw)
        transform, registration = _run_affine_registration(fixed, moving, seed)
        warped_mask = sitk.Resample(
            moving_mask, fixed, transform, sitk.sitkNearestNeighbor, 0, sitk.sitkUInt8
        )
        fixed_mask = sitk.OtsuThreshold(fixed, 0, 1)
        otsu_dice = dice(
            sitk.GetArrayViewFromImage(warped_mask), sitk.GetArrayViewFromImage(fixed_mask)
        )
        affine = transform.GetBackTransform()
        determinant = float(np.linalg.det(np.asarray(affine.GetMatrix()).reshape(3, 3)))
        metric = float(registration.GetMetricValue())
        passed = (
            geometry_ok
            and otsu_dice >= ANATOMY_OTSU_DICE_MIN
            and metric <= ANATOMY_METRIC_MAX
            and AFFINE_DETERMINANT_RANGE[0] <= determinant <= AFFINE_DETERMINANT_RANGE[1]
        )
        subject_dir = output_dir / subject
        subject_dir.mkdir(parents=True, exist_ok=True)
        sitk.WriteTransform(transform, str(subject_dir / "template_to_T2.tfm"))
        warped_labels = sitk.Resample(
            moving_labels,
            fixed,
            transform,
            sitk.sitkNearestNeighbor,
            0,
            moving_labels.GetPixelID(),
        )
        sitk.WriteImage(warped_labels, str(subject_dir / "atlas_in_T2.nii.gz"))
        row = {
            "subject": subject,
            "anatomy_sha256": sha256_file(path),
            "geometry_ok": geometry_ok,
            "otsu_dice": float(otsu_dice),
            "metric_value": metric,
            "affine_determinant": determinant,
            "status": "ANATOMY_REGISTRATION_PASS" if passed else "ANATOMY_REGISTRATION_FAIL",
        }
        rows.append(row)
        print(f"[{len(rows)}/12] {subject}: {row['status']}", flush=True)
    all_pass = all(row["status"] == "ANATOMY_REGISTRATION_PASS" for row in rows)
    return {
        "algorithm": "rigid-plus-affine-mattes-mi-v1",
        "outcome_data_used": False,
        "thresholds": {
            "otsu_dice_min": ANATOMY_OTSU_DICE_MIN,
            "metric_value_max": ANATOMY_METRIC_MAX,
            "affine_determinant_range": list(AFFINE_DETERMINANT_RANGE),
        },
        "subjects": rows,
        "status": "DEVELOPMENT_ANATOMY_GATE_PASS" if all_pass else "DEVELOPMENT_ANATOMY_GATE_FAIL",
    }


def mean_baseline_epi(subject_root: Path, trials_per_site: int = 5) -> object:
    """Average only the preregistered 0:40-s prestimulation volumes."""
    import SimpleITK as sitk

    total: np.ndarray | None = None
    reference = None
    count = 0
    for site in SITES:
        files = sorted(
            (subject_root / f"func_{site}").glob("*.nii.gz"),
            key=lambda path: int(path.name.removesuffix(".nii.gz")),
        )[:trials_per_site]
        if len(files) != trials_per_site:
            raise ValueError(f"expected {trials_per_site} baseline files for {site}")
        for path in files:
            image = sitk.ReadImage(str(path), sitk.sitkFloat32)
            if image.GetSize() != (96, 48, 18, 120):
                raise ValueError(f"unexpected EPI geometry: {path}")
            values = sitk.GetArrayViewFromImage(image)[:40].mean(axis=0, dtype=np.float64)
            total = values.copy() if total is None else total + values
            if reference is None:
                reference = sitk.Extract(image, (96, 48, 18, 0), (0, 0, 0, 0))
            count += 1
    assert total is not None and reference is not None
    baseline = sitk.GetImageFromArray(np.asarray(total / count, dtype=np.float32))
    baseline.CopyInformation(reference)
    return baseline


def write_epi_t2_qc(epi: object, t2_in_epi: object, path: Path) -> None:
    """Write a compact red/green axial overlay for human apparatus inspection."""
    from PIL import Image
    import SimpleITK as sitk

    def normalize(values: np.ndarray) -> np.ndarray:
        low, high = np.percentile(values, (2, 98))
        return np.clip((values - low) / max(high - low, 1e-12), 0.0, 1.0)

    epi_values = normalize(sitk.GetArrayViewFromImage(epi))
    t2_values = normalize(sitk.GetArrayViewFromImage(t2_in_epi))
    tiles = []
    for section in (3, 5, 7, 9, 11, 13):
        rgb = np.zeros((*epi_values[section].shape, 3), dtype=np.uint8)
        rgb[..., 0] = np.asarray(255 * t2_values[section], dtype=np.uint8)
        rgb[..., 1] = np.asarray(255 * epi_values[section], dtype=np.uint8)
        tiles.append(rgb)
    rows = [np.concatenate(tiles[index : index + 3], axis=1) for index in (0, 3)]
    montage = np.concatenate(rows, axis=0)
    image = Image.fromarray(montage).resize(
        (montage.shape[1] * 3, montage.shape[0] * 3), Image.Resampling.NEAREST
    )
    image.save(path)


def tune_epi_registration(
    development_root: Path,
    registration_root: Path,
    subject: str = "Thy1-sub05",
    seed: int = 42,
    mode: str = "affine",
) -> dict[str, object]:
    """Tune linear EPI-to-T2 coregistration on one outcome-blind baseline image."""
    import SimpleITK as sitk

    epi = scale_spacing_preserve_center(mean_baseline_epi(development_root / subject))
    t2 = scale_spacing_preserve_center(
        sitk.ReadImage(str(development_root / subject / "anat" / "T2w.nii.gz"), sitk.sitkFloat32)
    )
    if mode not in {"rigid", "affine"}:
        raise ValueError(f"unsupported EPI registration mode: {mode}")
    runner = _run_rigid_registration if mode == "rigid" else _run_affine_registration
    transform, registration = runner(epi, t2, seed)
    t2_mask = sitk.OtsuThreshold(t2, 0, 1)
    t2_in_epi = sitk.Resample(t2, epi, transform, sitk.sitkLinear, 0.0, sitk.sitkFloat32)
    warped_t2_mask = sitk.Resample(
        t2_mask, epi, transform, sitk.sitkNearestNeighbor, 0, sitk.sitkUInt8
    )
    epi_mask = sitk.OtsuThreshold(epi, 0, 1)
    overlap = dice(
        sitk.GetArrayViewFromImage(epi_mask), sitk.GetArrayViewFromImage(warped_t2_mask)
    )
    affine = transform.GetBackTransform()
    determinant = float(np.linalg.det(np.asarray(affine.GetMatrix()).reshape(3, 3)))
    subject_dir = registration_root / subject
    atlas_t2 = sitk.ReadImage(str(subject_dir / "atlas_in_T2.nii.gz"))
    atlas_epi = sitk.Resample(
        atlas_t2, epi, transform, sitk.sitkNearestNeighbor, 0, atlas_t2.GetPixelID()
    )
    sitk.WriteImage(epi, str(subject_dir / "baseline_epi.nii.gz"))
    sitk.WriteImage(t2_in_epi, str(subject_dir / "T2_in_EPI.nii.gz"))
    sitk.WriteImage(atlas_epi, str(subject_dir / "atlas_in_EPI.nii.gz"))
    sitk.WriteTransform(transform, str(subject_dir / "EPI_to_T2.tfm"))
    write_epi_t2_qc(epi, t2_in_epi, subject_dir / "EPI_T2_qc.png")
    return {
        "subject": subject,
        "algorithm": f"baseline-mean-{mode}-mattes-mi-v1",
        "baseline_seconds": [0, 40],
        "trials_per_site": 5,
        "outcome_data_used": False,
        "otsu_dice": float(overlap),
        "metric_value": float(registration.GetMetricValue()),
        "affine_determinant": determinant,
        "optimizer_stop": registration.GetOptimizerStopConditionDescription(),
    }


def register_development_epi(
    development_root: Path,
    registration_root: Path,
) -> dict[str, object]:
    def passes(row: dict[str, object]) -> bool:
        return (
            row["otsu_dice"] >= EPI_OTSU_DICE_MIN
            and row["metric_value"] <= EPI_METRIC_MAX
            and EPI_AFFINE_DETERMINANT_RANGE[0]
            <= row["affine_determinant"]
            <= EPI_AFFINE_DETERMINANT_RANGE[1]
        )

    rows = []
    for subject in (subject for cohort in DEVELOPMENT.values() for subject in cohort):
        primary = tune_epi_registration(development_root, registration_root, subject, mode="affine")
        chosen = primary
        fallback = None
        if not passes(primary):
            fallback = tune_epi_registration(development_root, registration_root, subject, mode="rigid")
            chosen = fallback
        row = dict(chosen)
        row["status"] = "EPI_REGISTRATION_PASS" if passes(row) else "EPI_REGISTRATION_FAIL"
        row["primary_attempt"] = primary
        row["fallback_attempt"] = fallback
        rows.append(row)
        print(f"[{len(rows)}/12] {subject}: {row['status']}", flush=True)
    all_pass = all(row["status"] == "EPI_REGISTRATION_PASS" for row in rows)
    return {
        "algorithm": "baseline-mean-affine-with-rigid-fallback-v1",
        "outcome_data_used": False,
        "thresholds": {
            "otsu_dice_min": EPI_OTSU_DICE_MIN,
            "metric_value_max": EPI_METRIC_MAX,
            "affine_determinant_range": list(EPI_AFFINE_DETERMINANT_RANGE),
        },
        "subjects": rows,
        "status": "DEVELOPMENT_EPI_GATE_PASS" if all_pass else "DEVELOPMENT_EPI_GATE_FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--algorithm", choices=("rigid", "affine"), default="rigid")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--download-root", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--register-development", action="store_true")
    parser.add_argument("--registration-output", type=Path)
    parser.add_argument("--tune-epi-subject")
    parser.add_argument("--epi-mode", choices=("rigid", "affine"), default="affine")
    parser.add_argument("--register-development-epi", action="store_true")
    args = parser.parse_args()
    if args.manifest and not args.download_root:
        parser.error("--manifest requires --download-root")
    downloads = None
    if args.manifest:
        downloads = download_development_anatomy(args.manifest, args.download_root, args.workers)
    audit = verify_assets(args.assets)
    if not audit["ok"]:
        result = {"asset_audit": audit, "status": "ASSET_HASH_GATE_FAIL"}
    else:
        runner = register_rigid_sample if args.algorithm == "rigid" else register_affine_sample
        sample, _ = runner(args.assets)
        result = {"asset_audit": audit, "sample_registration": sample, "status": sample["status"]}
    if downloads is not None:
        result["development_anatomy_downloads"] = downloads
    if args.register_development:
        if not args.download_root or not args.registration_output:
            parser.error("--register-development requires --download-root and --registration-output")
        development = register_development_anatomy(
            args.assets, args.download_root, args.registration_output
        )
        result["development_anatomy_registration"] = development
        if development["status"] != "DEVELOPMENT_ANATOMY_GATE_PASS":
            result["status"] = development["status"]
    if args.tune_epi_subject:
        if not args.download_root or not args.registration_output:
            parser.error("--tune-epi-subject requires --download-root and --registration-output")
        result["epi_registration_tuning"] = tune_epi_registration(
            args.download_root, args.registration_output, args.tune_epi_subject, mode=args.epi_mode
        )
    if args.register_development_epi:
        if not args.download_root or not args.registration_output:
            parser.error("--register-development-epi requires --download-root and --registration-output")
        epi_development = register_development_epi(args.download_root, args.registration_output)
        result["development_epi_registration"] = epi_development
        if epi_development["status"] != "DEVELOPMENT_EPI_GATE_PASS":
            result["status"] = epi_development["status"]
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
