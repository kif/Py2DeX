__author__ = 'Clemens Prescher'
# -*- coding: utf8 -*-
# Py2DeX - GUI program for fast processing of 2D X-ray data
# Copyright (C) 2014  Clemens Prescher (clemens.prescher@gmail.com)
# GSECARS, University of Chicago
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
from PyQt4 import QtGui, QtCore
from Data.HelperModule import SignalFrequencyLimiter
import numpy as np


class IntegrationImageController(object):
    def __init__(self, working_dir, view, img_data, mask_data,
                 calibration_data):
        self.working_dir = working_dir
        self.view = view
        self.img_data = img_data
        self.mask_data = mask_data
        self.calibration_data = calibration_data
        self._reset_img_levels = False
        self._first_plot = True

        self.view.show()
        self.initialize()
        self.img_data.subscribe(self.update_img)
        self.create_signals()
        self.create_mouse_behavior()

    def initialize(self):
        self.update_img(True)
        self.plot_mask()
        self.view.img_view.img_view_box.autoRange()

    def plot_img(self, reset_img_levels=None):
        if reset_img_levels is None:
            reset_img_levels = self._reset_img_levels
        if self._first_plot is True:
            reset_img_levels = True
            if self.img_data.get_img_data().sum() > 0:
                self._first_plot = False

        self.view.img_view.plot_image(self.img_data.get_img_data(),
                                      reset_img_levels)
        if reset_img_levels:
            self.view.img_view.auto_range()

    def plot_cake(self, reset_img_levels=None):
        if reset_img_levels is None:
            reset_img_levels = self._reset_img_levels
        self.view.img_view.plot_image(
            self.calibration_data.cake_img, reset_img_levels)
        if reset_img_levels:
            self.view.img_view.auto_range()

    def plot_mask(self):
        if self.view.mask_use_cb.isChecked() and \
                self.view.image_rb.isChecked():
            self.view.img_view.plot_mask(self.mask_data.get_img())
        else:
            self.view.img_view.plot_mask(
                np.zeros(self.mask_data.get_img().shape))

    def change_mask_colormap(self):
        if self.view.mask_transparent_cb.isChecked():
            self.view.img_view.set_color([255, 0, 0, 100])
        else:
            self.view.img_view.set_color([255, 0, 0, 255])
        self.plot_mask()

    def change_img_levels_mode(self):
        self.view.img_view.img_histogram_LUT.percentageLevel = \
            self.view.img_levels_percentage_rb.isChecked()
        self.view.img_view.img_histogram_LUT.old_hist_x_range = \
            self.view.img_view.img_histogram_LUT.hist_x_range
        self.view.img_view.img_histogram_LUT.first_image = False

    def create_signals(self):
        self.connect_click_function(self.view.next_img_btn, self.load_next_img)
        self.connect_click_function(
            self.view.prev_img_btn, self.load_previous_img)
        self.connect_click_function(
            self.view.load_img_btn, self.load_file_btn_click)
        self.connect_click_function(
            self.view.auto_img_btn, self.auto_img_btn_click)
        self.connect_click_function(
            self.view.img_browse_by_name_rb, self.set_iteration_mode_number)
        self.connect_click_function(
            self.view.img_browse_by_time_rb, self.set_iteration_mode_time)
        self.connect_click_function(
            self.view.mask_use_cb, self.mask_use_cb_changed)
        self.connect_click_function(
            self.view.mask_transparent_cb, self.change_mask_colormap)
        self.connect_click_function(
            self.view.img_levels_absolute_rb, self.change_img_levels_mode)
        self.connect_click_function(
            self.view.img_levels_percentage_rb, self.change_img_levels_mode)
        self.connect_click_function(self.view.image_rb, self.change_view_mode)
        self.connect_click_function(self.view.cake_rb, self.change_view_mode)

        self.connect_click_function(
            self.view.image_load_calibration_btn, self.load_calibration)
        self.create_auto_process_signal()

    def create_mouse_behavior(self):
        self.view.img_view.add_left_click_observer(self.img_mouse_click)
        self.mouse_pos_limiter = SignalFrequencyLimiter(self.view.img_view.add_mouse_move_observer,
                                                        self.show_img_mouse_position, 150)

    def connect_click_function(self, emitter, function):
        self.view.connect(emitter, QtCore.SIGNAL('clicked()'), function)

    def load_file_btn_click(self, filename=None):
        if filename is None:
            filename = str(QtGui.QFileDialog.getOpenFileName(
                self.view, "Load image data",
                self.working_dir['image']))

        if filename is not '':
            self.working_dir['image'] = os.path.dirname(filename)
            self.img_data.load(filename)
            self.plot_img()

    def mask_use_cb_changed(self):
        self.plot_mask()
        self.img_data.notify()

    def load_next_img(self):
        self.img_data.load_next()

    def load_previous_img(self):
        self.img_data.load_previous_file()

    def auto_img_btn_click(self):
        if self.calibration_data.is_calibrated:
            cake_state = self.view.cake_rb.isChecked()
            if cake_state:
                self.view.image_rb.setChecked(True)
                QtGui.QApplication.processEvents()

            while self.img_data.load_next():
                print 'integrated ' + self.img_data.filename
            print 'finished!'

            if cake_state:
                self.view.cake_rb.setChecked(True)
                QtGui.QApplication.processEvents()
                self.update_img()

    def update_img(self, reset_img_levels=False):
        self.view.img_filename_lbl.setText(
            os.path.basename(self.img_data.filename))
        if self.view.cake_rb.isChecked() and \
                self.calibration_data.is_calibrated:
            if self.view.mask_use_cb.isChecked():
                mask = self.mask_data.get_mask()
            else:
                mask = None
            self.calibration_data.integrate_2d(mask)
            self.plot_cake()
            self.view.img_view.plot_mask(
                np.zeros(self.mask_data.get_img().shape))
            self.view.img_view.activate_vertical_line()
            self.view.img_view.img_view_box.setAspectLocked(False)
        else:
            self.plot_img(reset_img_levels)
            self.plot_mask()
            self.view.img_view.deactivate_vertical_line()
            self.view.img_view.img_view_box.setAspectLocked(True)

    def change_view_mode(self):
        if self.view.cake_rb.isChecked() and \
                not self.calibration_data.is_calibrated:
            self.view.image_rb.setChecked(True)
        else:
            self.update_img()
            if self.view.cake_rb.isChecked():
                self.view.img_view.deactivate_circle_scatter()
                self._update_cake_line_pos()
            else:
                self.view.img_view.activate_circle_scatter()
                self._update_image_scatter_pos()

    def _update_cake_line_pos(self):
        cur_tth = self.view.spectrum_view.pos_line.getPos()[0]
        if cur_tth < np.min(self.calibration_data.cake_tth):
            new_pos = np.min(self.calibration_data.cake_tth)
        else:
            upper_ind = np.where(self.calibration_data.cake_tth > cur_tth)
            lower_ind = np.where(self.calibration_data.cake_tth < cur_tth)

            spacing = self.calibration_data.cake_tth[upper_ind[0][0]] - \
                      self.calibration_data.cake_tth[lower_ind[-1][-1]]
            new_pos = lower_ind[-1][-1] + \
                      (cur_tth -
                       self.calibration_data.cake_tth[lower_ind[-1][-1]]) / spacing
        self.view.img_view.vertical_line.setValue(new_pos)

    def _update_image_scatter_pos(self):
        cur_tth = self.view.spectrum_view.pos_line.getPos()[0]
        self.view.img_view.set_circle_scatter_tth(
            self.calibration_data.geometry._ttha, cur_tth / 180 * np.pi)

    def show_img_mouse_position(self, x, y):
        try:
            if x > 0 and y > 0:
                x_pos_string = 'X:  %4d' % x
                y_pos_string = 'Y:  %4d' % y
                self.view.mouse_x_lbl.setText(x_pos_string)
                self.view.mouse_y_lbl.setText(y_pos_string)

                int_string = 'I:   %5d' % self.view.img_view.img_data[
                    np.floor(y), np.floor(x)]
                self.view.mouse_int_lbl.setText(int_string)
                if self.calibration_data.is_calibrated:
                    x_temp = x
                    x = np.array([y])
                    y = np.array([x_temp])
                    if self.view.cake_rb.isChecked():
                        tth = self.calibration_data.cake_tth[np.round(y[0])]
                        azi = self.calibration_data.cake_azi[np.round(x[0])]
                        q_value = 4 * np.pi * np.sin(
                            tth / 360.0 * np.pi) / \
                                  self.calibration_data.geometry.wavelength / 1e10

                    else:
                        tth = self.calibration_data.geometry.tth(x, y)[0]
                        tth = tth / np.pi * 180.0
                        q_value = self.calibration_data.geometry.qFunction(
                            x, y) / 10.0
                        azi = self.calibration_data.geometry.chi(
                            x, y)[0] / np.pi * 180

                    azi = azi + 360 if azi < 0 else azi
                    d = self.calibration_data.geometry.wavelength / \
                        (2 * np.sin(tth / 180. * np.pi * 0.5)) * 1e10
                    tth_str = u'2θ:%9.2f  ' % tth
                    self.view.mouse_tth_lbl.setText(tth_str)
                    self.view.mouse_d_lbl.setText(u'd:%9.2f  ' % d)
                    self.view.mouse_q_lbl.setText(u'Q:%9.2f  ' % q_value)
                    self.view.mouse_azi_lbl.setText(u'X:%9.2f  ' % azi)
        except (IndexError, AttributeError):
            pass


    def img_mouse_click(self, x, y):
        #update click position
        # self.mouse_timer_function() #update the mouse position fields
        try:
            x_pos_string = 'X:  %4d' % y
            y_pos_string = 'Y:  %4d' % x
            int_string = 'I:   %5d' % self.view.img_view.img_data[
                np.floor(x), np.floor(y)]
            self.view.click_x_lbl.setText(x_pos_string)
            self.view.click_y_lbl.setText(y_pos_string)
            self.view.click_int_lbl.setText(int_string)
        except IndexError:
            self.view.click_int_lbl.setText('I: ')

        if self.view.cake_rb.isChecked():  # cake mode
            y = np.array([y])
            tth = self.calibration_data.cake_tth[np.round(y[0])]
            if self.view.spec_unit_q_rb.isChecked():
                q = 4 * np.pi * \
                    np.sin(tth / 360.0 * np.pi) / \
                    self.calibration_data.geometry.wavelength / 1e10
                self.view.spectrum_view.set_pos_line(q)
            else:
                self.view.spectrum_view.set_pos_line(tth)
        else:  # image mode
            x = np.array([x])
            y = np.array([y])
            if self.calibration_data.is_calibrated:
                tth = self.calibration_data.geometry.tth(x, y)[0]
                self.view.img_view.set_circle_scatter_tth(
                    self.calibration_data.geometry._ttha, tth)
                if self.view.spec_unit_q_rb.isChecked():
                    q = 4 * np.pi * \
                        np.sin(tth / 2) / \
                        self.calibration_data.geometry.wavelength / 1e10
                    self.view.spectrum_view.set_pos_line(q)
                else:
                    self.view.spectrum_view.set_pos_line(tth / np.pi * 180)

        self.view.click_tth_lbl.setText(self.view.mouse_tth_lbl.text())
        self.view.click_d_lbl.setText(self.view.mouse_d_lbl.text())
        self.view.click_q_lbl.setText(self.view.mouse_q_lbl.text())
        self.view.click_azi_lbl.setText(self.view.mouse_azi_lbl.text())

    def set_iteration_mode_number(self):
        self.img_data.file_iteration_mode = 'number'

    def set_iteration_mode_time(self):
        self.img_data.file_iteration_mode = 'time'

    def load_calibration(self, filename=None):
        if filename is None:
            filename = str(QtGui.QFileDialog.getOpenFileName(
                self.view, caption="Load calibration...",
                directory=self.working_dir[
                    'calibration'],
                filter='*.poni'))
        if filename is not '':
            self.working_dir['calibration'] = os.path.dirname(filename)
            self.calibration_data.load(filename)
            self.view.calibration_lbl.setText(
                self.calibration_data.calibration_name)
            self.img_data.notify()

    def create_auto_process_signal(self):
        self.view.autoprocess_cb.clicked.connect(self.auto_process_cb_click)
        self.autoprocess_timer = QtCore.QTimer(self.view)
        self.autoprocess_timer.setInterval(50)
        self.view.connect(self.autoprocess_timer,
                          QtCore.SIGNAL('timeout()'),
                          self.check_files)

    def auto_process_cb_click(self):
        if self.view.autoprocess_cb.isChecked():
            self._files_before = dict(
                [(f, None) for f in os.listdir(self.working_dir['image'])])
            self.autoprocess_timer.start()
        else:
            self.autoprocess_timer.stop()

    def check_files(self):
        self._files_now = dict(
            [(f, None) for f in os.listdir(self.working_dir['image'])])
        self._files_added = [
            f for f in self._files_now if not f in self._files_before]
        self._files_removed = [
            f for f in self._files_before if not f in self._files_now]
        if len(self._files_added) > 0:
            new_file_str = self._files_added[-1]
            path = os.path.join(self.working_dir['image'], new_file_str)
            acceptable_file_endings = ['.img', '.sfrm', '.dm3', '.edf', '.xml',
                                       '.cbf', '.kccd', '.msk', '.spr', '.tif',
                                       '.mccd', '.mar3450', '.pnm']
            read_file = False
            for ending in acceptable_file_endings:
                if path.endswith(ending):
                    read_file = True
                    break
            file_info = os.stat(path)
            if file_info.st_size > 100:
                if read_file:
                    self.load_file_btn_click(path)
                self._files_before = self._files_now
