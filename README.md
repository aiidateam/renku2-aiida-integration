# Exploring MCA AiiDA archives on RenkuLab v2

This repository contains the necessary infrastructure to explore AiiDA archives from Materials Cloud Archive via
RenkuLab v2:

**data**
- Empty directory with `.gitkeep`, to which the archive file will be downloaded when the RenkuLab session is started

**notebooks/explore.ipynb**
- Startup notebook

**startup.sh**
- Startup script that calls `post-init.sh` and the `jupyter server`

**post-init.sh**
- Archive download and AiiDA profile creation
