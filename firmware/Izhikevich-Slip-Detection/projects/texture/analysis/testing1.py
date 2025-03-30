import sys
sys.path.append('../../../framework/libraries/general')
sys.path.append('../../../framework/libraries/neuromorphic')
sys.path.append('../../../framework/libraries/iLimb')
sys.path.append('../../../framework/libraries/texture_recognition')
import texture
# import texture

textureRecog = texture.TextureRecognition()
ret = textureRecog.loadHeader('exp_dataset_newnatural_noise_30.txt')
if ret:
    textureRecog.createDatasetFiles()
    textureRecog.runProcessing(parallel=True)
else:
    print('fail')
