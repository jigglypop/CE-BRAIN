"""Stage 3J AFNI motion-corrected opto-fMRI time-kernel diagnostic."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np

from examples.brain.ce_brain_stage3f_optofmri_state_rdm import (
    DEVELOPMENT,
    SITES,
    exact_signflip_p,
    load_nifti,
)
from examples.brain.ce_brain_stage3g_optofmri_physical_distance import _load_epi_atlas
from examples.brain.ce_brain_stage3i_optofmri_time_kernel import (
    BASELINE,
    RESPONSE,
    analyze,
    percent_trajectory,
    response_rdms,
)


AFNI_ARCHIVE_SHA256 = "032e490a285c91331668b97c85e9adc67e5e73367cb5b7507da384e183c228e6"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wsl_path(path: Path) -> str:
    completed = subprocess.run(
        ["wsl.exe", "-d", "Ubuntu", "--exec", "wslpath", "-a", str(path.resolve())],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def motion_correct(
    source: Path,
    destination: Path,
    motion_file: Path,
    displacement_file: Path,
    afni_root: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    executable = f"{wsl_path(afni_root)}/3dvolreg"
    subprocess.run(
        [
            "wsl.exe",
            "-d",
            "Ubuntu",
            "--exec",
            "env",
            "AFNI_COMPRESSOR=GZIP",
            executable,
            "-Fourier",
            "-twopass",
            "-zpad",
            "4",
            "-base",
            "39",
            "-prefix",
            wsl_path(destination),
            "-1Dfile",
            wsl_path(motion_file),
            "-maxdisp1D",
            wsl_path(displacement_file),
            wsl_path(source),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _motion_summary(motion_file: Path, displacement_file: Path) -> dict[str, float]:
    motion = np.loadtxt(motion_file, ndmin=2)
    displacement = np.loadtxt(displacement_file, ndmin=1)
    return {
        "max_abs_rotation_deg": float(np.max(np.abs(motion[:, :3]))),
        "max_abs_translation_mm": float(np.max(np.abs(motion[:, 3:]))),
        "max_displacement_mm": float(np.max(displacement)),
        "median_displacement_mm": float(np.median(displacement)),
    }


def subject_result(
    subject: str,
    input_root: Path,
    registration_root: Path,
    afni_root: Path,
    workers: int = 4,
) -> dict[str, object]:
    paths_by_site: dict[str, list[Path]] = {}
    with tempfile.TemporaryDirectory(prefix=f"ce-{subject}-motion-") as temporary:
        temp_root = Path(temporary)
        corrected_by_site: dict[str, list[Path]] = {}
        baselines = []
        motion_rows = []
        jobs = []
        for site in SITES:
            sources = sorted(
                (input_root / subject / f"func_{site}").glob("*.nii.gz"),
                key=lambda path: int(path.name.removesuffix(".nii.gz")),
            )[:5]
            if len(sources) != 5:
                raise ValueError(f"expected five trials: {subject} {site}")
            paths_by_site[site] = sources
            corrected_by_site[site] = [Path()] * len(sources)
            for index, source in enumerate(sources, 1):
                output = temp_root / f"{site}_{index}.nii.gz"
                motion_file = temp_root / f"{site}_{index}_motion.1D"
                displacement_file = temp_root / f"{site}_{index}_displacement.1D"
                jobs.append((site, index, source, output, motion_file, displacement_file))

        def run_job(job: tuple[str, int, Path, Path, Path, Path]):
            site, index, source, output, motion_file, displacement_file = job
            motion_correct(source, output, motion_file, displacement_file, afni_root)
            data = load_nifti(output)
            if data.shape != (96, 48, 18, 120):
                raise ValueError(f"unexpected corrected shape {data.shape}: {source}")
            return (
                site,
                index,
                output,
                data[..., BASELINE].mean(axis=3),
                {"site": site, "trial": index, **_motion_summary(motion_file, displacement_file)},
            )

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_job, job) for job in jobs]
            for completed, future in enumerate(as_completed(futures), 1):
                site, index, output, baseline, motion = future.result()
                corrected_by_site[site][index - 1] = output
                baselines.append(baseline)
                motion_rows.append(motion)
                print(f"  {subject}: {completed}/{len(jobs)} trials", flush=True)

        subject_baseline = np.mean(baselines, axis=0)
        positive = subject_baseline[subject_baseline > 0]
        threshold = 0.20 * float(np.percentile(positive, 95))
        atlas_epi = _load_epi_atlas(registration_root / subject / "atlas_in_EPI.nii.gz")
        mask = (atlas_epi > 0) & (subject_baseline > threshold)
        if int(mask.sum()) < 1000:
            raise ValueError(f"registered brain mask too small: {subject}")

        odd = []
        even = []
        for site in SITES:
            trials = [percent_trajectory(load_nifti(path), mask) for path in corrected_by_site[site]]
            odd.append(np.mean([trials[0], trials[2], trials[4]], axis=0).reshape(-1))
            even.append(np.mean([trials[1], trials[3]], axis=0).reshape(-1))
        odd_rdm, even_rdm, cross_rdm = response_rdms(np.stack(odd), np.stack(even))
        from scipy.stats import spearmanr

        return {
            "subject": subject,
            "genotype": subject.split("-", 1)[0],
            "mask_voxels": int(mask.sum()),
            "time_samples": RESPONSE.stop - RESPONSE.start,
            "repeat_reliability": float(spearmanr(odd_rdm, even_rdm).statistic),
            "odd_rdm": odd_rdm.tolist(),
            "even_rdm": even_rdm.tolist(),
            "cross_half_rdm": cross_rdm.tolist(),
            "motion": sorted(motion_rows, key=lambda row: (SITES.index(row["site"]), row["trial"])),
        }


def add_motion_diagnostic(result: dict[str, object], raw: dict[str, object]) -> dict[str, object]:
    raw_by_subject = {row["subject"]: row for row in raw["subjects"]}
    rows = list(result["subjects"])
    deltas = np.asarray(
        [
            row["repeat_reliability"] - raw_by_subject[row["subject"]]["repeat_reliability"]
            for row in rows
            if row["genotype"] == "VGAT"
        ],
        dtype=float,
    )
    p_value = exact_signflip_p(deltas)
    vg_repeat = result["gates"]["VGAT"]
    result["vgat_motion_explanation"] = {
        "reliability_deltas": deltas.tolist(),
        "median_delta": float(np.median(deltas)),
        "signflip_p": p_value,
        "passed": bool(vg_repeat["passed"] and np.median(deltas) >= 0.10 and p_value <= 0.05),
    }
    result["status"] = (
        "VGAT_MOTION_EXPLANATION_CANDIDATE"
        if result["vgat_motion_explanation"]["passed"]
        else "VGAT_MOTION_EXPLANATION_NOT_ESTABLISHED"
    )
    result["slice_timing_correction_applied"] = False
    result["slice_timing_reason"] = "public NIfTI and paper do not specify acquisition timing/order"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--registration-root", type=Path, required=True)
    parser.add_argument("--afni-root", type=Path, required=True)
    parser.add_argument("--afni-archive", type=Path, required=True)
    parser.add_argument("--raw-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if sha256(args.afni_archive) != AFNI_ARCHIVE_SHA256:
        raise ValueError("AFNI archive hash mismatch")
    rows = []
    for genotype in ("Thy1", "VGAT"):
        for subject in DEVELOPMENT[genotype]:
            print(f"motion-correcting {subject}", flush=True)
            rows.append(
                subject_result(
                    subject,
                    args.input_root,
                    args.registration_root,
                    args.afni_root,
                    workers=args.workers,
                )
            )
    result = add_motion_diagnostic(
        analyze(rows), json.loads(args.raw_result.read_text(encoding="utf-8"))
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "gates": result["gates"], "vgat_motion_explanation": result["vgat_motion_explanation"]}, indent=2))


if __name__ == "__main__":
    main()
