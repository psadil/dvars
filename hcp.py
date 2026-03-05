import argparse
from pathlib import Path
import re
import logging


import nibabel as nb
import pydantic

from pymrimisc import motion


logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s", level=logging.INFO
)


class DVARS(pydantic.BaseModel):
    src: Path
    dst_root: Path

    @property
    def sub_id(self) -> str:
        sub = re.findall(r"\d{7,6}", str(self.src))
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
            / "0.parquet"
        )

    def process_run(self) -> None:
        if self.dst.exists():
            logging.info(f"{self.dst} already exists--skipping")
            return

        nii = nb.loadsave.load(self.src)
        motion.get_dvars(nii.get_fdata()).lazy().sink_parquet(  # type: ignore
            self.dst, mkdir=True
        )


def main(i: int, src: Path, dst_root: Path):
    subs = []
    for sub in src.glob("*"):
        if sub.is_dir():
            subs.append(sub)
    subs.sort()
    to_process = Path(subs[i])
    logging.info(f"Processing {to_process}")
    for img in (to_process / "MNINonLinear" / "Results").glob("*MRI_*_*/*dtseries.nii"):
        dvars = DVARS(src=img, dst_root=dst_root)
        logging.info(f"Will write to {dvars.dst}")
        dvars.process_run()

    logging.info("finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("i", type=int)
    parser.add_argument("src", type=Path)
    parser.add_argument("dst_root", type=Path)

    args = parser.parse_args()
    main(i=args.i, src=args.src, dst_root=args.dst_root)
