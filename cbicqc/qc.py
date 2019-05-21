# !/usr/bin/env python
#
# QC analysis node for nipype
# - derive class from
#
# USAGE : stats.py <QC Directory>
#
# AUTHOR : Mike Tyszka
# PLACE  : Caltech
# DATES  : 04/01/2013 JMT From scratch
#          10/24/2013 JMT Expand to calculate all stats
#          03/03/2014 JMT Add scanner name argument
#
# This file is part of CBICQC.
#
#    CBICQC is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    CBICQC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#   along with CBICQC.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2013-2014 California Institute of Technology.


from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

import nibabel as nb


class CBICQCInputSpec(BaseInterfaceInputSpec):

    in_file = File(exists=True,
                   desc='Motion corrected QC volume series',
                   mandatory=True)

    # Example scalar float input
    # threshold = traits.Float(desc='everything below this value will be set to zero',
    #                          mandatory=True)


class CBICQCOutputSpec(TraitedSpec):

    roi_mask = File(exists=False, desc="Phantom ROI mask")
    roi_timeseries = File(exists=False, desc="Timeseries for each ROI")


class CBICQC(BaseInterface):

    input_spec = CBICQCInputSpec
    output_spec = CBICQCOutputSpec

    def _run_interface(self, runtime):

        import numpy as np
        import pandas as pd

        qc_fname = self.inputs.in_file

        # Load QC motion corrected 4D data
        qc_nii = nb.load(qc_fname)
        qc_data = np.array(qc_nii.get_data())

        # Create 3D ROI mask
        mask_data = np.ones(qc_data.shape[0:2])

        mask_fname, ts_fname = self._output_fnames()

        # Save ROI mask
        mask_nii = nb.Nifti1Image(mask_data, qc_nii.get_affine())
        nb.save(mask_nii, mask_fname)

        # Save ROI timeseries
        roi_ts_df = pd.DataFrame(np.random.randn(100,3))
        roi_ts_df.to_csv(ts_fname)

        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()

        mask_fname, ts_fname = self._output_fnames()
        outputs["roi_mask"] = mask_fname
        outputs["roi_timeseries"] = ts_fname

        return outputs

    def _output_fnames(self):

        qc_fname = self.inputs.in_file
        _, fstub, _ = split_filename(qc_fname)

        # Construct derived filenames
        mask_fname = fstub + '_mask.nii.gz'
        ts_fname = fstub + '_roi_timeseries.csv'

        return mask_fname, ts_fname


# # Main function
# def main():
#
#     # Load timeseries from QC directory
#     print('    Loading timeseries')
#     x = np.loadtxt(qc_ts_file)
#
#     # Parse timeseries into column vectors
#     phantom_t = x[:, 0]
#     nyquist_t = x[:, 1]
#     noise_t = x[:, 2]
#
#     # Volume number vector
#     nv = len(phantom_t)
#     v = np.linspace(0, nv - 1, nv)
#
#     #
#     # Fit detrending function
#     #
#
#     # Demean timeseries
#     phantom_mean = phantom_t.mean()
#     nyquist_mean = nyquist_t.mean()
#     noise_mean = noise_t.mean()
#
#     # Fit exp + linear model to demeaned timeseries
#     print('    Fitting exponential models')
#     phantom_opt, phantom_cov = curve_fit(explin, v, phantom_t - phantom_mean)
#     nyquist_opt, nyquist_cov = curve_fit(explin, v, nyquist_t - nyquist_mean)
#     noise_opt, noise_cov = curve_fit(explin, v, noise_t - noise_mean)
#
#     # Generate fitted curves
#     phantom_fit = explin(v, phantom_opt[0], phantom_opt[1], phantom_opt[2]) + phantom_mean
#     nyquist_fit = explin(v, nyquist_opt[0], nyquist_opt[1], nyquist_opt[2]) + nyquist_mean
#     noise_fit = explin(v, noise_opt[0], noise_opt[1], noise_opt[2]) + noise_mean
#
#     # Fit residuals
#     phantom_res = phantom_t - phantom_fit
#     nyquist_res = nyquist_t - nyquist_fit
#     noise_res = noise_t - noise_fit
#
#     # Residual Gaussian sigma estimation
#     # Assumes Gaussian white noise + sparse outlier spikes
#     # Use robust estimate of residual sd (MAD * 1.4826)
#     phantom_res_sigma = np.median(np.abs(phantom_res)) * 1.4826
#     nyquist_res_sigma = np.median(np.abs(nyquist_res)) * 1.4826
#     noise_res_sigma = np.median(np.abs(noise_res)) * 1.4826
#
#     # Count spikes, defined as residuals more than 5 SD from zero
#     phantom_spikes = (np.abs(phantom_res) > 5 * phantom_res_sigma).sum()
#     nyquist_spikes = (np.abs(nyquist_res) > 5 * nyquist_res_sigma).sum()
#     noise_spikes = (np.abs(noise_res) > 5 * noise_res_sigma).sum()
#
#     # Calculate percent drift over course of acquisition (use fitted curve)
#     phantom_drift = (phantom_fit[nv - 1] - phantom_fit[0]) / phantom_fit[0] * 100.0
#     nyquist_drift = (nyquist_fit[nv - 1] - nyquist_fit[0]) / nyquist_fit[0] * 100.0
#     noise_drift = (noise_fit[nv - 1] - noise_fit[0]) / noise_fit[0] * 100.0
#
#     # Append mean, spike count, drift to fit parameters
#     phantom_opt = np.append(phantom_opt, [phantom_mean, phantom_spikes, phantom_drift])
#     nyquist_opt = np.append(nyquist_opt, [nyquist_mean, nyquist_spikes, nyquist_drift])
#     noise_opt = np.append(noise_opt, [noise_mean, noise_spikes, noise_drift])
#
#     # SNR relative to mean noise
#     # Estimate spatial noise sigma (assuming underlying Gaussian and Half-Normal distribution)
#     # sigma = mean(noise) * sqrt(pi/2)
#     # See for example http://en.wikipedia.org/wiki/Half-normal_distribution
#
#     noise_sigma = noise_mean * sqrt(pi / 2)
#     phantom_snr = phantom_mean / noise_sigma
#     nyquist_snr = nyquist_mean / noise_sigma
#
#     # Generate detrended timeseries - add back constant offset for each ROI
#     phantom_0 = phantom_res + phantom_mean
#     nyquist_0 = nyquist_res + nyquist_mean
#     noise_0 = noise_res + noise_mean
#
#     # Create array with detrended timeseries in columns (for output by np.savetxt)
#     ts_detrend = np.array([phantom_0, nyquist_0, noise_0])
#     ts_detrend = ts_detrend.transpose()
#
#     # Create array with timeseries detrend parameters in rows for each model
#     # Parameter order : Exp amp, Exp tau, linear, const, spike count
#     stats_pars = np.row_stack([phantom_opt, nyquist_opt, noise_opt])
#
#     #
#     # Center of Mass
#     #
#
#     # Calculate center of mass of temporal mean image using fslstats -c
#     print('    Calculating center of mass of phantom')
#     com_cmd = ["fslstats", os.path.join(qc_dir, "qc_mean"), "-c"]
#     proc = subprocess.Popen(com_cmd, stdout=subprocess.PIPE)
#     out, err = proc.communicate()
#
#     # Split returned string and convert to floats
#     com_x, com_y, com_z = out.split()
#     com_x = float(com_x)
#     com_y = float(com_y)
#     com_z = float(com_z)
#
#     #
#     # Apparent motion parameters
#     #
#     print('    Analyzing motion parameters')
#     qc_mcf_parfile = os.path.join(qc_dir, 'qc_mcf.par')
#
#     if not os.path.isfile(qc_mcf_parfile):
#         print(qc_mcf_parfile + ' does not exist - exiting')
#         sys.exit(0)
#
#     # N x 6 array (6 motion parameters in columns)
#     x = np.loadtxt(qc_mcf_parfile)
#
#     # Extract displacement timeseries for each axis
#     dx = x[:, 3]
#     dy = x[:, 4]
#     dz = x[:, 5]
#
#     # Calculate max absolute displacements (in microns) for each axis
#     max_adx = (np.abs(dx)).max() * 1000.0
#     max_ady = (np.abs(dy)).max() * 1000.0
#     max_adz = (np.abs(dz)).max() * 1000.0
#
#     #
#     # Finalize stats array for writing
#     #
#
#     # Flatten stats array (phantom pars first, then nyquist, etc)
#     stats_pars = stats_pars.flatten()
#
#     # Add remaining stats to bottom of array
#     stats_pars = np.append(stats_pars, [phantom_snr, nyquist_snr, com_x, com_y, com_z, max_adx, max_ady, max_adz])
#
#     #
#     # Output results to files
#     #
#
#     # Save fit parameters
#     qc_stats_parfile = os.path.join(qc_dir, 'qc_stats.txt')
#     np.savetxt(qc_stats_parfile, stats_pars, delimiter=' ', fmt='%0.6f')
#
#     # Save detrended timeseries
#     print('    Writing detrended timeseries')
#     ts_detrend_file = os.path.join(qc_dir, 'qc_timeseries_detrend.txt')
#     np.savetxt(ts_detrend_file, ts_detrend, delimiter=' ', fmt='%0.6f')
#
#
#
#     # Done
#     print('  Finished python statistical analysis')
#
#
# # Exponential + linear detrending model
# def explin(t, a, tau, b):
#     return a * np.exp(-t / tau) + b * t
