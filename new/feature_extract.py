import src.processing.signal_processing as utils
import yasa

delta = [0.5,4]
theta = [4,8]
alpha = [9,11]
sigma = [12,15]
beta1 = [14,20]
beta2 = [20,30]
beta = [14,30]
gamma1 = [30,40]
gamma2 = [40,49.5]
gamma = [30,49.5]
Kcomplex = [0.5,1]
bands = [delta,theta,alpha,sigma,beta,gamma,Kcomplex]

def exfeature(data,fs=512):
    features = []
    for band in bands:
        band_data = utils.filter_bandpass(data, band, fs)
        pfd = utils.petrosian_fd(band_data) #petrosian fractal dimension
        SE = utils.spectral_entropy(band_data,fs)
        SD = utils.standard_deviation(band_data)
        HA = utils.hjorth_activity(band_data)
        HM = utils.hjorth_mobility(band_data)
        HC = utils.hjorth_complexity(band_data)
        LRSSV = utils.lrssv(band_data)
        features.extend([pfd,SE,SD,HA,HM,HC,LRSSV])
    spindles = yasa.spindles_detect(data,sf=1000)
    if spindles is not None:
        num_spindle = len(spindles.summary())
        if num_spindle > 0:
            yesspindle = 1
        else:
            yesspindle = 0
    else:
        yesspindle = 0
    features.append(yesspindle)
    return features
