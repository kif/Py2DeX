# Py2DeX - GUI program for fast processing of 2D X-ray data
# Copyright (C) 2014  Clemens Prescher (clemens.prescher@gmail.com)
# GSECARS, University of Chicago
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.


__author__ = 'Clemens Prescher'

import os
from PyQt4 import QtGui, QtCore
import numpy as np
from Data.HelperModule import get_base_name
import pyqtgraph as pg


class IntegrationPhaseController(object):
    def __init__(self, working_dir, view, calibration_data,
                 spectrum_data, phase_data):
        self.working_dir = working_dir
        self.view = view
        self.calibration_data = calibration_data
        self.spectrum_data = spectrum_data
        self.phase_data = phase_data
        self.phase_lw_items = []
        self.create_signals()

    def create_signals(self):
        self.connect_click_function(self.view.phase_add_btn, self.add_phase)
        self.connect_click_function(self.view.phase_del_btn, self.del_phase)
        self.connect_click_function(
            self.view.phase_clear_btn, self.clear_phases)

        self.view.phase_pressure_step_txt.editingFinished.connect(
            self.update_phase_pressure_step)
        self.view.phase_temperature_step_txt.editingFinished.connect(
            self.update_phase_pressure_step)

        self.view.phase_pressure_sb.valueChanged.connect(
            self.phase_pressure_sb_changed)
        self.view.phase_temperature_sb.valueChanged.connect(
            self.phase_temperature_sb_changed)

        self.view.phase_lw.currentItemChanged.connect(self.phase_item_changed)

        self.spectrum_data.subscribe(self.update_intensities)
        self.view.spectrum_view.view_box.sigRangeChangedManually.connect(self.update_intensities_slot)
        self.view.spectrum_view.spectrum_plot.autoBtn.clicked.connect(self.spectrum_auto_btn_clicked)

    def connect_click_function(self, emitter, function):
        self.view.connect(emitter, QtCore.SIGNAL('clicked()'), function)

    def add_phase(self, filename=None):
        if filename is None:
            filenames = QtGui.QFileDialog.getOpenFileNames(
                self.view, "Load Phase(s).", self.working_dir['phase'])
            if len(filenames):
                self.working_dir['phase'] = os.path.dirname(str(filenames[0]))
                for filename in filenames:
                    filename = str(filename)
                    self.phase_data.add_phase(filename)
                    self.phase_lw_items.append(
                        self.view.phase_lw.addItem(get_base_name(filename)))
                    if self.view.phase_apply_to_all_cb.isChecked():
                        self.phase_data.phases[-1].compute_d(
                            pressure=np.float(
                                self.view.phase_pressure_sb.value()),
                            temperature=np.float(
                                self.view.phase_temperature_sb.value()))
                    self.phase_data.get_lines_d(-1)
                    self.view.phase_lw.setCurrentRow(
                        len(self.phase_data.phases) - 1)
                    self.add_phase_plot()
        else:
            self.phase_data.add_phase(filename)
            self.phase_lw_items.append(
                self.view.phase_lw.addItem(get_base_name(filename)))
            if self.view.phase_apply_to_all_cb.isChecked():
                self.phase_data.phases[-1].compute_d(
                    pressure=np.float(self.view.phase_pressure_sb.value()),
                    temperature=np.float(
                        self.view.phase_temperature_sb.value()))
            self.phase_data.get_lines_d(-1)
            self.view.phase_lw.setCurrentRow(len(self.phase_data.phases) - 1)
            self.add_phase_plot()
            self.working_dir['phase'] = os.path.dirname(str(filename))

    def add_phase_plot(self):
        axis_range = self.view.spectrum_view.spectrum_plot.viewRange()
        x_range = axis_range[0]
        y_range = axis_range[1]
        positions, intensities, baseline = \
            self.phase_data.rescale_reflections(
                -1, self.spectrum_data.spectrum,
                x_range, y_range,
                self.calibration_data.geometry.wavelength * 1e10,
                self.get_unit())
        self.view.spectrum_view.add_phase(self.phase_data.phases[-1].name,
                                          positions,
                                          intensities,
                                          baseline)

    def del_phase(self):
        cur_ind = self.view.phase_lw.currentRow()
        if cur_ind >= 0:
            self.view.phase_lw.takeItem(cur_ind)
            self.phase_data.del_phase(cur_ind)
            self.view.spectrum_view.del_phase(cur_ind)

    def clear_phases(self):
        while self.view.phase_lw.count() > 0:
            self.del_phase()

    def update_phase_pressure_step(self):
        value = np.float(self.view.phase_pressure_step_txt.text())
        self.view.phase_pressure_sb.setSingleStep(value)

    def update_phase_temperature_step(self):
        value = np.float(self.view.phase_temperature_step_txt.text())
        self.view.phase_temperature_sb.setSingleStep(value)

    def phase_pressure_sb_changed(self, val):
        if self.view.phase_apply_to_all_cb.isChecked():
            for ind in xrange(self.view.phase_lw.count()):
                self.phase_data.set_pressure(ind, np.float(val))
            self.update_intensities()

        else:
            cur_ind = self.view.phase_lw.currentRow()
            self.phase_data.set_pressure(cur_ind, np.float(val))
            self.update_intensity(cur_ind)

    def phase_temperature_sb_changed(self, val):
        if self.view.phase_apply_to_all_cb.isChecked():
            for ind in xrange(self.view.phase_lw.count()):
                self.phase_data.set_temperature(ind, np.float(val))
            self.update_intensities()

        else:
            cur_ind = self.view.phase_lw.currentRow()
            self.phase_data.set_temperature(cur_ind, np.float(val))
            self.update_intensity(cur_ind)

    def phase_item_changed(self):
        cur_ind = self.view.phase_lw.currentRow()
        pressure = self.phase_data.phases[cur_ind].pressure
        temperature = self.phase_data.phases[cur_ind].temperature

        self.view.phase_pressure_sb.blockSignals(True)
        self.view.phase_temperature_sb.blockSignals(True)
        self.view.phase_pressure_sb.setValue(pressure)
        self.view.phase_temperature_sb.setValue(temperature)
        self.view.phase_pressure_sb.blockSignals(False)
        self.view.phase_temperature_sb.blockSignals(False)

    def update_intensities_slot(self, *args):
        axis_range = self.view.spectrum_view.spectrum_plot.viewRange()
        self.view.spectrum_view.spectrum_plot.disableAutoRange()
        self.update_intensities(axis_range)

        x_range = axis_range[0]
        y_range = axis_range[1]
        x, y = self.spectrum_data.spectrum.data
        if x_range[0] <= np.min(x) and x_range[1] >= np.max(x) and \
                        y_range[0] <= np.min(y) and y_range[1] >= np.max(y):
            self.view.spectrum_view.spectrum_plot.enableAutoRange()

    def update_intensity(self, ind, axis_range=None):
        if axis_range is None:
            axis_range = self.view.spectrum_view.spectrum_plot.viewRange()
        x_range = axis_range[0]
        y_range = axis_range[1]
        positions, intensities, baseline = \
            self.phase_data.rescale_reflections(
                ind, self.spectrum_data.spectrum,
                x_range, y_range,
                self.calibration_data.geometry.wavelength * 1e10,
                self.get_unit())
        self.view.spectrum_view.update_phase_intensities(
            ind, positions, intensities, baseline)

    def update_intensities(self, axis_range=None):
        self.view.spectrum_view.view_box.blockSignals(True)
        for ind in xrange(self.view.phase_lw.count()):
            self.update_intensity(ind, axis_range)
        self.view.spectrum_view.view_box.blockSignals(False)
        self.view.spectrum_view.update_phase_line_visibilities()

    def connect_spectrum(self):
        self.view.spectrum_view.spectrum_plot.sigRangeChanged.connect(
            self.update_intensities_slot)

    def get_unit(self):
        if self.view.spec_tth_btn.isChecked():
            return 'tth'
        elif self.view.spec_q_btn.isChecked():
            return 'q'
        elif self.view.spec_d_btn.isChecked():
            return 'd'


    def spectrum_auto_btn_clicked(self):
        """
        Runs self.update_intensities_slot after 50 ms.
        This is needed because the graph scaling is to slow, to call update_intensities immediately after the autoscale-btn
        was clicked
        """
        QtCore.QTimer.singleShot(50, self.update_intensities_slot)

