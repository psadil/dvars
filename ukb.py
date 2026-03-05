import argparse
from pathlib import Path
import re
import logging

from pymrimisc import motion


from nilearn import maskers
import pydantic


logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
)


class DVARS(pydantic.BaseModel):
    src: Path
    dst_root: Path

    @property
    def mask(self) -> Path:
        return self.src.parent / "mask.nii.gz"

    @property
    def sub_id(self) -> str:
        sub = re.findall(r"\d{7}", str(self.src))
        if not (len(sub) == 1):
            msg = f"Unexpected length of sub_id for {self.src}"
            raise RuntimeError(msg)

        return sub[0]

    @property
    def ses_id(self) -> str:
        ses = re.findall(r"(?<=ses-)\d+", str(self.src))
        if not (len(ses) == 1):
            msg = f"Unexpected length of ses_id for {self.src}"
            raise RuntimeError(msg)

        return ses[0]

    @property
    def src_id(self) -> str:
        stem = self.src.name.removesuffix(".gz").removesuffix(".nii")
        if "20227" in str(self.src):
            datatype = "20227"
        elif "20249" in str(self.src):
            datatype = "20249"
        else:
            msg = "Unknown file"
            raise RuntimeError(msg)
        return f"{datatype}-{stem}"

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

        mask = maskers.NiftiMasker(mask_img=self.mask)
        out = mask.fit_transform(self.src)
        motion.get_dvars(out).drop("value").lazy().sink_parquet(self.dst, mkdir=True)


def main(i: int, src: Path, dst_root: Path):
    subs = [sub for sub in src.read_text().splitlines()]
    to_process = Path(subs[i])
    logging.info(f"Processing {to_process}")
    for ses in [2, 3]:
        for datatype in ["20249", "20227"]:
            for data in (
                to_process / f"ses-{ses}" / "non-bids" / datatype / "fMRI"
            ).glob("*MRI*/filtered_func_*.nii.gz"):
                dvars = DVARS(src=data, dst_root=dst_root)
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
