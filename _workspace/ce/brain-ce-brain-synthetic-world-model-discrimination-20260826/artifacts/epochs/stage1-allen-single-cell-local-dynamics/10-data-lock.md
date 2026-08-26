# Stage 1 Allen immutable data lock

Status: COMPLETE / SCHEMA_ONLY

- Specimen: `320654829`
- Ephys result/session: `320654827`
- Well-known file: `491201608`
- Filename: `320654827_ephys.nwb`
- Bytes: `53,057,893`
- SHA-256: `fd164a3091fbbb3be358238088afa2e2f08981d49edffa87d55309931a9853ab`
- ETag: `546d9396f5b40`
- NWB/pipeline: `NWB-1.0.5` / IVSCC `1.0`
- Sampling: 200,000 Hz for every selected sweep
- Units: response `Volts`, stimulus `Amps`
- Raw valid start: `150,000` inclusive for every selected sweep

Allen SDK semantics use inclusive stop `start+count-1`. Counts are:

- Long Square 33--54 and 56--59: `1,054,001` each;
- Ramp 5: `997,844`; Ramp 6: `1,321,863`;
- Noise 1 60/62/64 and Noise 2 61/63: `4,854,001` each.

After the frozen factor-20 alignment, each Long Square has 52,700 bins, Ramp 5
49,892, Ramp 6 66,093, and each Noise sweep 242,700. This receipt opened no
response/stimulus data values and computed no model endpoint.
