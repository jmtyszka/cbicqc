#!/opt/local/bin/python
# Detrend signal in a CBIC QA timeseries text file
#
# AUTHOR : Mike Tyszka
# PLACE  : Caltech
# DATES  : 04/01/2013 JMT From scratch

import sys
import os
import numpy as np
from pylab import *
from scipy.optimize import curve_fit

# Main function
def main():
    
    # Report python version
    # print(sys.version_info)
    # print(sp.__version__)
    
    # QA root directory
    qa_root = '/Library/Server/Web/Data/Sites/Default/QA'
    
    # Get QA date from command line args
    if len(sys.argv) >= 2:
        qa_dir = sys.argv[1]
    else:
        qa_dir = os.getcwd()
    
    print('Detrending ' + qa_dir)

    # Construct timeseries filename
    qa_ts_file = os.path.join(qa_root,qa_dir,'qa_timeseries.txt')
    if not os.path.isfile(qa_ts_file):
        print(qa_ts_file + ' does not exist - exiting')
        sys.exit(0)

    # Load timeseries from QA directory
    print('Loading timeseries')
    x = np.loadtxt(qa_ts_file)

    # Parse timeseries into column vectors
    phantom_t = x[:,0]
    nyquist_t = x[:,1]
    noise_t   = x[:,2]

    # Volume number vector
    nv = len(phantom_t)
    v = np.linspace(0, nv-1, nv)

    # Fit exp + const model to each timeseries
    print('Fitting exponential models')
    phantom_opt, phantom_cov = curve_fit(expconst, v, phantom_t)
    nyquist_opt, nyquist_cov = curve_fit(expconst, v, nyquist_t)
    noise_opt, noise_cov     = curve_fit(expconst, v, noise_t)

    # Generate fitted curves
    phantom_fit = expconst(v, phantom_opt[0], phantom_opt[1], phantom_opt[2], phantom_opt[3])
    nyquist_fit = expconst(v, nyquist_opt[0], nyquist_opt[1], nyquist_opt[2], nyquist_opt[3])
    noise_fit   = expconst(v, noise_opt[0], noise_opt[1], noise_opt[2], noise_opt[3])

    # Fit residuals
    phantom_res = phantom_t - phantom_fit
    nyquist_res = nyquist_t - nyquist_fit
    noise_res = noise_t - noise_fit

    # Residual stats
    # Assumes Gaussian white noise + sparse outlier spikes
    # Use robust estimate of residual sd (MAD * 1.4826)
    phantom_res_sd = np.median(np.abs(phantom_res)) * 1.4826
    nyquist_res_sd = np.median(np.abs(nyquist_res)) * 1.4826
    noise_res_sd   = np.median(np.abs(noise_res)) * 1.4826

    # Count spikes, defined as residuals more than 5 SD from zero
    phantom_spikes = (np.abs(phantom_res) > 5 * phantom_res_sd).sum()
    nyquist_spikes = (np.abs(nyquist_res) > 5 * nyquist_res_sd).sum()
    noise_spikes   = (np.abs(noise_res) > 5 * noise_res_sd).sum()

    # Append sd and spike count to fit parameter list
    phantom_opt = np.append(phantom_opt, [phantom_res_sd, phantom_spikes])
    nyquist_opt = np.append(nyquist_opt,[nyquist_res_sd, nyquist_spikes])
    noise_opt   = np.append(noise_opt,[noise_res_sd, noise_spikes])

    # Generate detrended timeseries
    phantom_0 = phantom_res + phantom_opt[3]
    nyquist_0 = nyquist_res + nyquist_opt[3]
    noise_0   = noise_res + noise_opt[3]

    # Create array with detrended timeseries in columns (for output by np.savetxt
    ts_detrend = np.array([phantom_0, nyquist_0, noise_0])
    ts_detrend = ts_detrend.transpose()

    # Save detrended timeseries
    print('Writing detrended timeseries')
    ts_detrend_file = os.path.join(qa_root,qa_dir,'qa_timeseries_detrend.txt')
    np.savetxt(ts_detrend_file, ts_detrend, delimiter=' ',fmt='%0.6f')

    # Create array with timeseries detrend parameters in columns for each model
    # Row order : Exp amp, Exp tau, linear, const, residual sd, spike count
    detrend_pars = np.array([phantom_opt, nyquist_opt, noise_opt])
    detrend_pars = detrend_pars.transpose()

    # Save fit parameters
    print('Writing detrending parameters')
    qa_detrend_pars = os.path.join(qa_root,qa_dir,'qa_detrend.pars')
    np.savetxt(qa_detrend_pars, detrend_pars, delimiter=' ',fmt='%0.6f')

    # Plot figures

    fig = figure(figsize = (10,8))

    subplot(311, title='Phantom')
    plot(v, phantom_t, 'ro', v, phantom_fit, '-b', v, phantom_0, '-g')
    subplot(312, title='Nyquist Ghost')
    plot(v, nyquist_t, 'ro', v, nyquist_fit, '-b', v, nyquist_0, '-g')
    subplot(313, title='Noise')
    plot(v, noise_t,   'ro', v, noise_fit,   '-b', v, noise_0,   '-g')

    # Adjust vertical spacing to allow for titles
    subplots_adjust(hspace = 0.5)

    # Save figure in QA directory
    savefig(os.path.join(qa_root,qa_dir,'qa_detrend.png'))

# Exponential + constant model
def expconst(t, a, tau, b, c):
    return a * np.exp(-t/tau) + b * t + c

# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
