config.detection.thresholdValue=5.0
config.doDecorrelation=True

#config.doSelectSources=False

from lsst.ip.diffim.getTemplate import GetCalexpAsTemplateTask
config.getTemplate.retarget(GetCalexpAsTemplateTask)  
