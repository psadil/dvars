# dvars

Repo for calculating DVARS in data stored on JHPCE

## Structure

Files are stored as arrow datasets. 

```{shell}
$ tree -L 5 dvars | head
dvars
├── dataset=HCPAgingRec
│   ├── sub=6002236
│   │   └── ses=1
│   │       ├── src=rfMRI_REST1_AP_Atlas_MSMAll_hp0_clean
│   │       │   └── dvars.arrow
│   │       ├── src=rfMRI_REST1_PA_Atlas_MSMAll_hp0_clean
│   │       │   └── dvars.arrow
│   │       ├── src=rfMRI_REST2_AP_Atlas_MSMAll_hp0_clean
│   │       │   └── dvars.arrow
```

Each file is a table

|  t|        A|        D|         S|        DPD|         ZD|    DVARS|dataset |     sub| ses|src                            |
|--:|--------:|--------:|---------:|----------:|----------:|--------:|:-------|-------:|---:|:------------------------------|
|  1| 3.784818| 1.985132| 0.2807895| -6.1827153| -4.6384849| 2.817895|ukb     | 5902812|   2|20227-filtered_func_data_clean |
|  2| 4.727538| 2.182186| 0.5185044| -2.7343983|  2.0862912| 2.954445|ukb     | 5902812|   2|20227-filtered_func_data_clean |
|  3| 4.715485| 2.297970| 0.6058910| -0.7082396|  0.5208611| 3.031811|ukb     | 5902812|   2|20227-filtered_func_data_clean |
|  4| 4.787917| 2.285580| 0.6165337| -0.9250505|  0.6858148| 3.023627|ukb     | 5902812|   2|20227-filtered_func_data_clean |
|  5| 5.249457| 2.357410| 0.6653134|  0.3319351| -0.2623765| 3.070772|ukb     | 5902812|   2|20227-filtered_func_data_clean |
|  6| 5.497924| 2.396127| 0.7443832|  1.0094449| -0.7654791| 3.095885|ukb     | 5902812|   2|20227-filtered_func_data_clean |

- t: volume
- A: total ("all") variability
- D: Fast ("difference") variability
- S: Slow ("average") variability
- DPD: "delta percent D", excess variance in the signal change as a percentage of the mean (total) signal change
- ZD: z-score for signal change
- DVARS: raw DVARS (likely not useful)

For interpretation, see [Afouni & Nichols (2018)](https://doi.org/10.1016/j.neuroimage.2017.12.098) and [Pham et al. (2023)](https://doi.org/10.1016/j.neuroimage.2023.119972).

Calculations for various dvars measures based on [fMRIscrub](https://github.com/mandymejia/fMRIscrub).

## Import 

In python, try [polars.scan_ips](https://docs.pola.rs/api/python/stable/reference/api/polars.scan_ipc.html#polars.scan_ipc)

```{python}
import polars as pl
pl.scan_ipc("derivatives/dvars").filter(pl.col("dataset")=="ukb").collect()
```

In R, try [arrow::open_dataset](https://arrow.apache.org/docs/r/reference/open_dataset.html)

```{R}
arrow::open_dataset("/Users/psadil/data/dvars/derivatives/dvars", format = "ipc") |> 
  filter(t > 0, dataset == "ukb") |>
  dplyr::collect()
```



# Datasets

## HCPAgingRec

### Script

[hcpaging](hcpaging)

### Notes

- Files with `src` containing "hp#" were provided by the HCP after (at least some) high-pass filtering, and no additional filtering was done before calculating DVARS
- Files with `src` containing "clean" were provided by the HCP after ICA FIX-ing, and no additional cleaning was done before calculating DVARS

### Dataset Documentation

https://humanconnectome.org/study/hcp-lifespan-aging


## HCPDevelopmentRec

### Script

[hcpadev](hcpdev) 


### Notes

- Files with `src` containing "hp#" were provided by the HCP after (at least some) high-pass filtering, and no additional filtering was done before calculating DVARS
- Files with `src` containing "clean" were provided by the HCP after ICA FIX-ing, and no additional cleaning was done before calculating DVARS


### Dataset Documentation

https://humanconnectome.org/study/hcp-lifespan-development


## ukb

### Script

[ukb](ukb)


### Notes

- The UKB provides data that have already undergone high-pass filtering and so no additional cleaning was done before calculating DVARS
- The resting state vs task scans can be identified with the src entity
  - src=20227-filtered_func_data_clean: resting state (after ICA FIX'ing)
  - 'src=20249-filtered_func_data: task scans

### Dataset Documentation

https://biobank.ndph.ox.ac.uk/showcase/download.cgi

