import argparse
from pathlib import Path
import re
import logging


import nibabel as nb
import numpy as np
from nilearn import signal
import pydantic

from pymrimisc import dvars


logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
)


class DVARS(pydantic.BaseModel):
    src: Path
    dst_root: Path

    @property
    def sub_id(self) -> str:
        sub = re.findall(r"\d{7}", str(self.src))
        if not (len(sub) == 1):
            msg = f"Unexpected length of sub_id for {self.src}"
            raise RuntimeError(msg)

        return sub[0]

    @property
    def ses_id(self) -> str:
        return "1"

    @property
    def src_id(self) -> str:
        return self.src.name.removesuffix(".nii").removesuffix(".dtseries")

    @property
    def dst(self) -> Path:
        return (
            self.dst_root
            / f"sub={self.sub_id}"
            / f"ses={self.ses_id}"
            / f"src={self.src_id}"
            / "dvars.arrow"
        )

    def process_run(self) -> None:
        if self.dst.exists():
            logging.info(f"{self.dst} already exists--skipping")
            return
        if not (parent := self.dst.parent).exists():
            parent.mkdir(parents=True)

        nii = nb.loadsave.load(self.src)
        if "clean" in self.src.name:
            # data have already been cleaned
            dvars.get_dvars(nii.get_fdata()).write_ipc(  # type: ignore
                self.dst, compression="zstd"
            )
        else:
            logging.info("cleaning src before calculating DVARS")
            out: np.ndarray = signal.clean(
                signals=nii.get_fdata(),  # type: ignore
                detrend=True,
                standardize=False,  # type: ignore
                high_pass=0.008,
                t_r=0.72,
            )
            dvars.get_dvars(out).write_ipc(self.dst, compression="zstd")


def main(i: int, src: Path, dst_root: Path):
    subs = [sub for sub in src.read_text().splitlines()]
    to_process = Path(subs[i])
    logging.info(f"Processing {to_process}")
    for img in (to_process / "MNINonLinear" / "Results").glob(
        "*MRI_*_*/*dtseries.nii"
    ):
        dvars = DVARS(src=img, dst_root=dst_root)
        logging.info(f"Will write to {dvars.dst}")
        dvars.process_run()
    logging.info("completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("i", type=int)
    parser.add_argument("src", type=Path)
    parser.add_argument("dst_root", type=Path)

    args = parser.parse_args()
    main(i=args.i, src=args.src, dst_root=args.dst_root)
