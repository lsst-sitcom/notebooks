"""
To understand the file directory structure, it is helpful to consult 
https://confluence.lsstcorp.org/display/~hchiang2/S18+Output+dataset+types+for+HSC+tasks

and also Table 1 from Bosch et al. 2017
https://arxiv.org/abs/1705.06766

Note that in the example below, the registry contains many data products for which the files 
do not actually exist in the data repository
"""

import numpy as np
from matplotlib import pyplot as plt
plt.ion()

from lsst.daf.persistence import Butler

butler = Butler('/datasets/hsc/repo/rerun/RC/w_2018_10/DM-13647/')

# Get a particular calexp
# In order to find this file, I had to look through the directory structure
# $(pointing)/$(filter)/corr/CORR-$(visit)-$(ccd).fits

#subset = butler.subset('calexp', **{'ccd':95, 'pointing':1111, 'filter':'HSC-Z', 'visit':17962})
subset = butler.subset('calexp', **{'ccd':95, 'filter':'HSC-Z', 'visit':17962})
calexp = butler.get('calexp', **subset.cache[0])
src = butler.get('src', **subset.cache[0])

# Image
plt.figure(figsize=(5, 8))
plt.imshow(calexp.getImage().array, 
           vmin=np.percentile(calexp.getImage().array, 10), 
           vmax=np.percentile(calexp.getImage().array, 90))
plt.colorbar()
plt.scatter(src.getX(), src.getY(), c='red', s=2)

# Variance
plt.figure(figsize=(5, 8))
plt.imshow(calexp.getVariance().array,
           vmin=np.percentile(calexp.getVariance().array, 10),
           vmax=np.percentile(calexp.getVariance().array, 90))
plt.colorbar()

# The calexp contains many useful things, including
# 'getCalib',
# 'getDetector',
# 'getDimensions',
# 'getFilter',
# 'getHeight',
# 'getImage',
# 'getInfo',
# 'getMask',
# 'getMaskedImage',
# 'getMetadata',
# 'getPsf',
# 'getVariance',
# 'getWcs'

# Joint calibration products - not sure how to get these

# $(pointing)/$(filter)/corr/$(tract)/wcs-$(visit)-$(ccd).fits

#subset = butler.subset('wcs', tract=9813, filter='HSC-R')
#wcs = butler.get('wcs', dataId=**subset.cache[0])

# Deep coadd products

# Cosmos tract is 9813: https://jira.lsstcorp.org/browse/DM-13647
# Again, I had to look through the file directory structure to find this
# deepCoadd/$(filter)/$(tract)/$(patch)/calexp-$(filter)-$(tract)-$(patch).fits
dataid = {'filter':'HSC-I', 'tract': 9813, 'patch':'4,4'}
# deep coadd calexp seems to have many of the same functions as calexp
coadd_calexp = butler.get('deepCoadd_calexp', dataId=dataid)
coadd_forced_src = butler.get('deepCoadd_forced_src', dataId=dataid)
coadd_meas = butler.get('deepCoadd_meas', dataId=dataid)

# Get all the column names
# coadd_forced_src.getSchema().getNames()
