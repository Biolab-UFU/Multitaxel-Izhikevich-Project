# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering and Robotics Group
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#Paths
import os, sys, glob
sys.path.append('../../framework/libraries/general')
sys.path.append('../../framework/libraries/neuromorphic')
sys.path.append('../../framework/libraries/texture_recognition')
#-------------------------------------------------------------------------------
import numpy as np
import scipy.stats as stat
import scipy.signal as sig
import matplotlib.pyplot as plt
import spiking_neurons as spkn
import texture as textrecog
from statsmodels.nonparametric.kde import KDEUnivariate
#-------------------------------------------------------------------------------
createFile = False
#-------------------------------------------------------------------------------
if createFile:
    #header file that determines data processing
    fileHeader = 'load_artificial.txt'
    #create a TextureRecognition object
    textureRecog = textrecog.TextureRecognition()
    #loads the header file
    ret = textureRecog.loadHeader(fileHeader)
    if ret:
        #generates the name of the files that should be loaded
        textureRecog.createDatasetFiles()
        #runs the processing of data
        textureRecog.runProcessing(parallel=True)
else:
    # folderpath = './load_artificial'
    folderpath = '../texture/analysis/exp_dataset_natural_noise_10'
    resp = [np.load(folderpath + '/results_taxel' + str(k) + '.npz') for k in range(16)]
    numTextures = int(len(resp[0]['texturev']))
    numSignals = int(len(resp[0]['inputCurrent']) / numTextures)

    # auxv = 5
    # taxelId = 12
    # for taxelId in range(16):
    #     plt.figure(figsize=(19.2,10.8),dpi=100)
    #     auxv=0
    #     for w in range(numTextures):
    #         plt.subplot(numTextures,1,w+1)
    #         if w == 0:
    #             plt.title('Taxel ' + str(taxelId))
    #         plt.plot(resp[taxelId]['inputCurrent'][auxv],label=resp[taxelId]['texturev'][w])
    #         # plt.scatter(resp[taxelId]['spikes'][auxv],np.ones(len(resp[taxelId]['spikes'][auxv]))*0.2,color='k',marker='|')
    #         auxv += numSignals
    #     manager = plt.get_current_fig_manager()
    #     manager.resize(*manager.window.maxsize())
    #     filename = './inputs_taxel' + str(taxelId) + '.png'
    #     plt.savefig(filename, bbox_inches='tight')
    #     # plt.legend()
    #
    # #raw inputs
    # for taxelId in range(16):
    #     plt.figure(figsize=(19.2,10.8),dpi=100)
    #     auxv=0
    #     for w in range(numTextures):
    #         # plt.subplot(numTextures,1,w+1)
    #         if w == 0:
    #             plt.title('Taxel ' + str(taxelId))
    #         plt.plot(resp[taxelId]['inputCurrent'][auxv],label=resp[taxelId]['texturev'][w])
    #         # plt.scatter(resp[taxelId]['spikes'][auxv],np.ones(len(resp[taxelId]['spikes'][auxv]))*0.2,color='k',marker='|')
    #         auxv += numSignals
    #     plt.legend()
    #     manager = plt.get_current_fig_manager()
    #     manager.resize(*manager.window.maxsize())
    #     filename = './all_inputs_taxel' + str(taxelId) + '.png'
    #     plt.savefig(filename, bbox_inches='tight')
    #
    # auxv = 5
    # taxelId = 12
    # for taxelId in range(16):
    #     plt.figure(figsize=(19.2,10.8),dpi=100)
    #     auxv=0
    #     for w in range(numTextures):
    #         plt.subplot(numTextures,1,w+1)
    #         if w == 0:
    #             plt.title('Taxel ' + str(taxelId))
    #         plt.plot(resp[taxelId]['rawCurrent'][auxv],label=resp[taxelId]['texturev'][w])
    #         # plt.scatter(resp[taxelId]['spikes'][auxv],np.ones(len(resp[taxelId]['spikes'][auxv]))*0.2,color='k',marker='|')
    #         auxv += numSignals
    #     manager = plt.get_current_fig_manager()
    #     manager.resize(*manager.window.maxsize())
    #     filename = './inputs_raw_taxel' + str(taxelId) + '.png'
    #     plt.savefig(filename, bbox_inches='tight')
        # plt.legend()

    #raw inputs
    for taxelId in range(16):
        plt.figure(figsize=(19.2,10.8),dpi=100)
        auxv=0
        for w in range(numTextures):
            # plt.subplot(numTextures,1,w+1)
            if w == 0:
                plt.title('Taxel ' + str(taxelId))
            plt.plot(100*(resp[taxelId]['rawCurrent'][auxv])+10,label=resp[taxelId]['texturev'][w])
            # plt.scatter(resp[taxelId]['spikes'][auxv],np.ones(len(resp[taxelId]['spikes'][auxv]))*0.2,color='k',marker='|')
            auxv += numSignals
        plt.legend()
        manager = plt.get_current_fig_manager()
        manager.resize(*manager.window.maxsize())
        filename = './all_inputs_raw_taxel' + str(taxelId) + '.png'
        plt.savefig(filename, bbox_inches='tight')



    plt.show()
