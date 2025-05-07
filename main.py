import numpy as np

from chrdll4.chr_connection import *
from chrdll4.chr_cmd_id import *
from chrdll4.chr_dll import *
from chrdll4.chr_utils import *

from configparser import ConfigParser, NoOptionError
from tkinter.filedialog import asksaveasfilename
from typing import List, Union, Callable
from collections.abc import Iterable
from threading import Thread, Event
from loguru import logger as log
from queue import Queue, Full
from datetime import datetime
from time import sleep
import subprocess
import write_file
import timeit
import numpy
import os

from filter_handler import FilterHandler
from graphic import MainGUI, run_as_admin_faq


port = 7891
py_dir = os.path.dirname(__file__)
config = ConfigParser()
config.read('config/config.cfg')
conn_cb = None
Rsp = Union[Response, bool]
Args = List[str]
try:
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log.add('logs/log_{time}.log', format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", colorize=True)
except PermissionError:
    run_as_admin_faq()


class DataAcquisition(Thread):
    def __init__(self, conn: Connection = None, update_freq: int = 20, exp_sample_count=200):
        super().__init__()
        self.daemon = True
        self.conn = conn
        self._reading = Event()
        self._reading.clear()
        self._thread_on = Event()
        self.samples_collected = Event()
        self.freq = update_freq
        self.get_next_sample_count = exp_sample_count
        self._full_scale = 0
        self._get_last_sample_flag = False
        self.sig_ids = None
        self.last_distance_1_int16_ch1 = None
        self.last_distance_1_ch1 = None
        self.last_intensity_ch1 = None
        self.last_distance_1 = None
        self.last_intensity_1 = None
        self.last_sample_cnt = None
        self.encoder_x = None
        self.encoder_y = None
        self.encoder_z = None
        self.exposure_flags = None
        self.sample_cnt = None
        self.distance_1_int16 = None
        self.distance_1 = None
        self.intensity = None

    def run(self):
        log.info('Start GetNextSample DataAcquisition')
        self.samples_collected.set()
        self._thread_on.set()
        try:
            self.conn.flush_connection_buffer()
            flush = False
            while self._reading.is_set():
                if not (self.samples_collected.wait(1 / self.freq)):  # continue the while loop if timeout
                    continue
                try:
                    samples = self.conn.get_next_samples(sample_count=self.get_next_sample_count,
                                                         flush_buffer_on_error=flush)
                    flush = False
                    if samples is None and self._get_last_sample_flag:
                        self._get_last_sample_flag = False
                        samples = self.conn.get_last_sample()
                except ValueError:
                    log.exception('Get Next Sample Failed!')
                    continue
                except Exception as e:
                    log.error(f"Caught an exception: {str(e)}")
                    log.error("Will Flush the connection buffer before the next reading. Some data will be lost.")
                    flush = True
                    continue
                if samples is not None:
                    # log.info('[DataAcq] Samples OK')
                    self.sig_ids = [str(item[1]) for item in samples.signal_info]
                    self.last_sample_cnt = None
                    self.last_distance_1_int16_ch1 = None
                    self.last_distance_1_ch1 = None
                    self.last_intensity_ch1 = None
                    self.last_distance_1 = None
                    self.last_intensity_1 = None
                    self.encoder_x = None
                    self.encoder_y = None
                    self.encoder_z = None
                    self.exposure_flags = None
                    self.sample_cnt = None
                    self.distance_1_int16 = None
                    self.distance_1 = None
                    self.intensity = None
                    distance_coef = self._full_scale / 32768

                    """ Sample Count (id=83) """
                    if '83' in self.sig_ids:
                        self.sample_cnt = samples.get_signal_values_all(sig_id=83).astype('uint16')
                        self.last_sample_cnt = self.sample_cnt[-1]

                    """ Distance 1 int16 (id=16640) """
                    if '16640' in self.sig_ids:
                        if isinstance(samples.get_signal_values(sig_id=16640), Iterable):
                            self.last_distance_1_int16_ch1 = samples.get_signal_values(sig_id=16640)[0].astype('int16')
                        else:
                            self.last_distance_1_int16_ch1 = samples.get_signal_values(sig_id=16640).astype('int16')
                        self.distance_1_int16 = samples.get_signal_values_all(sig_id=16640).astype('int16')
                        self.last_distance_1_ch1 = self.last_distance_1_int16_ch1 * distance_coef
                        self.distance_1 = self.distance_1_int16 * distance_coef
                        self.last_distance_1 = self.distance_1[-1].astype('float32')

                    """ Intensity (id=16641) """
                    if '16641' in self.sig_ids:
                        if isinstance(samples.get_signal_values(sig_id=16641), Iterable):
                            self.last_intensity_ch1 = samples.get_signal_values(sig_id=16641)[0].astype('int16')
                        else:
                            self.last_intensity_ch1 = samples.get_signal_values(sig_id=16641).astype('int16')
                        self.intensity = samples.get_signal_values_all(sig_id=16641).astype('int16')
                        self.last_intensity_1 = self.intensity[-1]

                    """ Encoder X (id=65) """
                    if '65' in self.sig_ids:
                        self.encoder_x = samples.get_signal_values_all(sig_id=65).astype('int64')

                    """ Encoder Y (id=66) """
                    if '66' in self.sig_ids:
                        self.encoder_y = samples.get_signal_values_all(sig_id=66).astype('int64')

                    """ Encoder Z (id=67) """
                    if '67' in self.sig_ids:
                        self.encoder_z = samples.get_signal_values_all(sig_id=67).astype('int64')

                    """ Exposure Flags (id=76) """
                    if '76' in self.sig_ids:
                        self.exposure_flags = samples.get_signal_values_all(sig_id=76).astype('int16')

                    self.samples_collected.clear()
                else:
                    sleep(1 / self.freq)
                    # log.info('[DataAcq] samples is None.')
        except APIException as e:
            log.exception('Data Acquisition Error')
            self.stop_reading()
        log.info('GetNextSample DataAcquisition Closed')
        self._thread_on.clear()

    def set_full_scale(self, val: int):
        self._full_scale = val

    def start_reading(self):
        self._reading.set()

    def stop_reading(self):
        self._reading.clear()

    def set_get_next_sample_count(self, cnt: int):
        log.info('Set get next sample count = {}'.format(cnt))
        self.get_next_sample_count = cnt

    def get_last_sample(self):
        self._get_last_sample_flag = True

    def get_last_sample_count(self):
        if self.last_sample_cnt is not None:
            return self.last_sample_cnt
        else:
            return None

    def get_last_distance_1_int16_ch1(self):
        if self.last_distance_1_int16_ch1 is not None:
            return self.last_distance_1_int16_ch1
        else:
            return None

    def get_last_distance_1_ch1(self):
        if self.last_distance_1_ch1 is not None:
            return self.last_distance_1_ch1
        else:
            return None

    def get_last_intensity_ch1(self):
        if self.last_intensity_ch1 is not None:
            return self.last_intensity_ch1.copy()
        else:
            return None

    def get_last_distance_1(self):
        if self.last_distance_1 is not None:
            return self.last_distance_1.copy()
        else:
            return None

    def get_last_intensity_1(self):
        if self.last_intensity_1 is not None:
            return self.last_intensity_1.copy()
        else:
            return None

    def get_sample_count(self):
        if self.sample_cnt is not None:
            return self.sample_cnt
        else:
            return None

    def get_distance_1_int16(self):
        if self.distance_1_int16 is not None:
            return self.distance_1_int16
        else:
            return None

    def get_distance_1(self):
        if self.distance_1 is not None:
            return self.distance_1
        else:
            return None

    def get_intensity(self):
        if self.intensity is not None:
            return self.intensity
        else:
            return None

    def get_encoder_x(self):
        if self.encoder_x is not None:
            return self.encoder_x
        else:
            return None

    def get_encoder_y(self):
        if self.encoder_y is not None:
            return self.encoder_y
        else:
            return None

    def get_encoder_z(self):
        if self.encoder_z is not None:
            return self.encoder_z
        else:
            return None

    def get_exposure_flags(self):
        if self.exposure_flags is not None:
            return self.exposure_flags
        else:
            return None

    def thread_is_on(self) -> bool:
        return self._thread_on.is_set()


class AppProcess:
    def __init__(self):
        self.command_reference_path = os.path.join(py_dir, config.get('DocPath', 'api_reference'))
        self.api_reference_path = os.path.join(py_dir, config.get('DocPath', 'api_reference'))
        self.dll_path = os.path.join(py_dir, config.get('SoftwarePath', 'dll'))
        self.chr_explorer_path = os.path.join(py_dir, config.get('SoftwarePath', 'chr_explorer'))
        self.intensity_level_dir = os.path.join(py_dir, config.get('DocPath', 'intensity_level'))
        self.doc_path = {
            'datasheet': {
                'CLS': os.path.join(py_dir, config.get('Datasheet', 'CLS')),
                'CLS2': os.path.join(py_dir, config.get('Datasheet', 'CLS2')),
                'CLS 2Pro': os.path.join(py_dir, config.get('Datasheet', 'CLS2Pro')),
                'CVC': os.path.join(py_dir, config.get('Datasheet', 'CVC')),
                'Mini': os.path.join(py_dir, config.get('Datasheet', 'Mini')),
                'C': os.path.join(py_dir, config.get('Datasheet', 'C')),
                '2S': os.path.join(py_dir, config.get('Datasheet', '2S')),
                'Overall': os.path.join(py_dir, config.get('Datasheet', 'Overall')),
                'IT': os.path.join(py_dir, config.get('Datasheet', 'IT')),
                'DPS': os.path.join(py_dir, config.get('Datasheet', 'DPS')),
                'FSS80': os.path.join(py_dir, config.get('Datasheet', 'FSS80')),
                'FSS310': os.path.join(py_dir, config.get('Datasheet', 'FSS310'))
            },
            'user manual': {
                'CLS': os.path.join(py_dir, config.get('UserManual', 'CLS')),
                'CLS2': os.path.join(py_dir, config.get('UserManual', 'CLS2')),
                'CLS 2Pro': os.path.join(py_dir, config.get('UserManual', 'CLS2Pro')),
                'CVC': os.path.join(py_dir, config.get('UserManual', 'CVC')),
                'Mini': os.path.join(py_dir, config.get('UserManual', 'Mini')),
                'C': os.path.join(py_dir, config.get('UserManual', 'C')),
                '2S': os.path.join(py_dir, config.get('UserManual', '2S')),
                'IT': os.path.join(py_dir, config.get('UserManual', 'IT')),
                'DPS': os.path.join(py_dir, config.get('UserManual', 'DPS')),
                'FSS80': os.path.join(py_dir, config.get('UserManual', 'FSS80')),
                'FSS310': os.path.join(py_dir, config.get('UserManual', 'FSS310'))
            },
            'command manual': {
                'CLS': os.path.join(py_dir, config.get('CommandManual', 'CLS')),
                'CVC': os.path.join(py_dir, config.get('CommandManual', 'CVC')),
                'Mini': os.path.join(py_dir, config.get('CommandManual', 'Mini')),
                'C': os.path.join(py_dir, config.get('CommandManual', 'C')),
                '2S': os.path.join(py_dir, config.get('CommandManual', '2S')),
                'IT': os.path.join(py_dir, config.get('CommandManual', 'IT')),
                'DPS': os.path.join(py_dir, config.get('CommandManual', 'DPS')),
                'FSS': os.path.join(py_dir, config.get('CommandManual', 'IT')),
            },
            'api manual': os.path.join(py_dir, config.get('DocPath', 'api_reference'))
        }
        self.sample_code_dir = {
            'C#': {
                'general': os.path.join(py_dir, config.get('SampleCode Cs', 'general'))
            },
            'C++': {
                'general': os.path.join(py_dir, config.get('SampleCode Cpp', 'general'))
            },
            'Python': {
                'general': os.path.join(py_dir, config.get('SampleCode Python', 'general')),
            }
        }
        self._filter = FilterHandler(file_path='filter.xml')
        self._filter.load_filter()

    def get_filter_ip(self):
        return self._filter.get_ip()

    def set_filter_ip(self, val):
        self._filter.set_ip(val)

    def save_data_filter(self):
        self._filter.save_filter()

    def open_manual(self, manual_type, sensor):
        if manual_type == 'api manual':
            subprocess.Popen([self.doc_path[manual_type]], shell=True, start_new_session=True)
        else:
            subprocess.Popen([self.doc_path[manual_type][sensor]], shell=True, start_new_session=True)

    def open_sample_code(self, language):
        subprocess.Popen('explorer /select,{}'.format(self.sample_code_dir[language]['general']))

    def open_command_reference(self):
        subprocess.Popen([self.command_reference_path], shell=True)

    def open_api_reference(self):
        subprocess.Popen([self.api_reference_path], shell=True)

    def open_intensity_level_attachment(self):
        subprocess.Popen('explorer /select,{}'.format(self.intensity_level_dir))

    def open_chr_dll_dir(self):
        subprocess.Popen('explorer /select,{}'.format(self.dll_path))

    def open_chr_explorer_dir(self):
        subprocess.Popen('explorer /select,{}'.format(self.chr_explorer_path))


class App(MainGUI):
    def __init__(self) -> None:
        super().__init__()
        self._device_type = None
        self._device_index_map = {
            '0': DeviceType.CHR_MULTI_CHANNEL,
            '1': DeviceType.CHR_2,
            '2': DeviceType.CHR_COMPACT
        }
        self._conn_prc = None
        self._conn_cb = None
        self._chr_dll = load_client_dll()[1]
        self._app_prc = AppProcess()
        self._ip = self._app_prc.get_filter_ip()
        self._auto_search_dev_list = []
        self.init_gui()
        self._app_cb = AppCallback(master=self, app_prc=self._app_prc)
        self.set_app_callback()

    def init_gui(self):
        self.lf.conn_f.set_ip(self._ip)

    def conn_start_init(self) -> None:
        self._ip = self.lf.conn_f.get_ip()
        self._device_type = self._device_index_map[self.lf.sensor_type_f.get_sensor_type()]
        self._conn_prc = ConnProcess(master=self, ip=self._ip, device_type=self._device_type,
                                     conn_callback=self.conn_callback)
        self.set_conn_function_callback()
        self._conn_prc.start()

    # region AutoSearch

    def auto_conn(self) -> None:
        err = start_chr_device_auto_search(chr_dll=self._chr_dll, conn_type=2)
        if err == 0:
            self.lf.conn_f.set_auto_search_device_callback(cmd=self.check_auto_search_device)
            self.lf.conn_f.set_auto_conn_callback(cmd=self.auto_search_conn)
            self.lf.conn_f.set_cancel_callback(cmd=self.cancel_auto_search)
            self.lf.conn_f.disable_conn_button()
            self.lf.conn_f.disable_ip_entry()
            self.lf.conn_f.disable_auto_button()
        else:
            pass

    def check_auto_search_device(self):
        self._auto_search_dev_list = []
        result = False
        search_is_finished = is_chr_device_auto_search_finished(chr_dll=self._chr_dll)
        if search_is_finished:
            detected_dev, err = detected_chr_device_info(chr_dll=self._chr_dll)
            cancel_chr_device_auto_search(chr_dll=self._chr_dll)
            device_list = detected_dev.split(';')[:-1]
            dev_dict_list = []
            for dev in device_list:
                dev_dict = {k.strip(): v.strip() for k, v in (item.split(':') for item in dev.split(','))}
                with connection_from_params(addr=dev_dict['IP'], device_type=int(dev_dict['Device Type'])) as conn:
                    prsn = conn.send_command_string('PRSN ?').args[0]
                    prsn_dict = {}
                    for item in prsn.split():
                        item_list = item.split('=')
                        if len(item_list) == 2:
                            key, value = item_list
                            prsn_dict[key] = value
                    try:
                        # for all sensors
                        device_type = prsn_dict['personality.oem.devicetype']
                    except KeyError:
                        # for CLS 2
                        device_type = prsn_dict['oemdevicetype']
                dev_str = 'Device = {}, Serial No. = {}, (TCP/IP) IP = {}'.format(device_type, dev_dict['SNR'],
                                                                                  dev_dict['IP'])

                dev_dict_list.append(dev_str)
                self._auto_search_dev_list.append(dev_dict)
            result = dev_dict_list
        return result

    def cancel_auto_search(self):
        cancel_chr_device_auto_search(chr_dll=self._chr_dll)
        self.lf.conn_f.enable_ip_entry()
        self.lf.conn_f.enable_conn_button()
        self.lf.conn_f.enable_auto_button()

    def auto_search_conn(self):
        sel_index = self.lf.conn_f.auto_search_win.get_selected_option()
        ip = dict(self._auto_search_dev_list[sel_index])['IP']
        self.lf.conn_f.set_ip(ip)
        self.lf.conn_f.conn()

    # endregion

    def set_app_callback(self) -> None:
        self._app_cb.set_introduction_page_callback()
        self._app_cb.set_on_close_callback()
        self.lf.conn_f.set_conn_callback(cmd=self.conn_start_init)
        self.lf.conn_f.set_disconn_btn_callback(cmd=self.disconnect)
        self.lf.conn_f.set_auto_search_callback(cmd=self.auto_conn)

        """ Set top frame callback """
        self.tf.sample_rate_led_f.set_shz_entry_callback(cmd=self._app_cb.app_sample_rate_cmd)
        self.tf.device_measurement_mode_f.set_tf_trig_mode_sel_callback(cmd=self._app_cb.tf_trig_mode_select_cmd)
        self.mf.others_p.cls2_f.set_intensity_level_attachment_callback(cmd=self._app_cb.intensity_level_attachment_cmd)

        """ Set main frame trigger test page callback """
        self.mf.trigger_test_p.right_f.set_tt_trig_mode_sel_callback(cmd=self._app_cb.trig_test_mode_select_cmd)
        self.mf.trigger_test_p.right_f.set_use_encoder_trig_callback(cmd=self._app_cb.tt_use_encoder_trig_cmd)
        self.mf.trigger_test_p.right_f.set_tt_trig_on_return_callback(cmd=self._app_cb.tt_trig_on_return_cmd)
        self.mf.trigger_test_p.right_f.set_axis_sel_callback(cmd=self._app_cb.tt_axis_sel_cmd)
        # self.mf.trigger_test_p.right_f.set_axis_sel_callback(cmd=self._conn_cb.axis_sel_cmd)
        """ Set main frame trigger scan page callback """
        self.mf.trigger_scan_p.set_tc_trig_mode_sel_callback(cmd=self._app_cb.tc_mode_select_cmd)
        self.mf.trigger_scan_p.set_tc_axis_select_callback(cmd=self._app_cb.tc_axis_sel_cmd)
        self.mf.trigger_scan_p.set_tc_encoder_resolution_callback(cmd=self._app_cb.tc_encoder_resolution_cmd)
        self.mf.trigger_scan_p.set_tc_en_start_pos_callback(cmd=self._app_cb.tc_en_start_pos_cmd)
        self.mf.trigger_scan_p.set_tc_en_stop_pos_callback(cmd=self._app_cb.tc_en_stop_pos_cmd)
        self.mf.trigger_scan_p.set_tc_en_interval_callback(cmd=self._app_cb.tc_en_interval_cmd)
        self.mf.trigger_scan_p.set_tc_pos_start_pos_callback(cmd=self._app_cb.tc_pos_start_pos_cmd)
        self.mf.trigger_scan_p.set_tc_pos_stop_pos_callback(cmd=self._app_cb.tc_pos_stop_pos_cmd)
        self.mf.trigger_scan_p.set_tc_pos_interval_callback(cmd=self._app_cb.tc_pos_interval_cmd)
        self.mf.trigger_scan_p.set_x_scan_length_callback(cmd=self._app_cb.tc_x_scan_length_cmd)
        self.mf.trigger_scan_p.set_dx_callback(cmd=self._app_cb.tc_scan_dx_cmd)
        self.mf.trigger_scan_p.set_tc_trig_on_return_callback(cmd=self._app_cb.tc_trig_on_return_cmd)
        self.mf.trigger_scan_p.set_reset_ctn_callback(cmd=self._app_cb.tc_reset_ctn_cmd)

    def set_conn_function_callback(self) -> None:
        """ Set callback functions to the GUI class """
        """ Init the connection callback class """
        global conn_cb
        conn_cb = ConnCallback(master=self, conn_prc=self._conn_prc, app_callback=self._app_cb)
        self._conn_cb = conn_cb
        """ Set top frame callback """
        self.tf.output_signal_f.set_entry_callback(cmd=self._conn_cb.output_signal_cmd)
        self.tf.sample_rate_led_f.set_shz_entry_callback(cmd=self._conn_cb.sample_rate_cmd)
        self.tf.sample_rate_led_f.set_lai_entry_callback(cmd=self._conn_cb.led_cmd)
        self.tf.threshold_f.set_entry_callback(cmd=self._conn_cb.threshold_cmd)
        self.tf.device_measurement_mode_f.set_tf_trig_mode_sel_callback(cmd=self._conn_cb.tf_trig_mode_select_cmd)
        self.tf.device_data_flow_switch_f.set_flow_switch_sel_callback(cmd=self._conn_cb.tf_flow_switch_select_cmd)
        """ Set left frame callback """
        self.lf.dark_ref_f.set_dark_callback(cmd=self._conn_cb.dark_cmd)
        self.lf.dark_ref_f.set_fast_dark_callback(cmd=self._conn_cb.fast_dark_cmd)
        self.lf.probe_sel_f.set_probe_select_callback(cmd=self._conn_cb.probe_select_cmd)
        self.lf.multilayer_stn_f.set_number_of_peak_callback(cmd=self._conn_cb.number_of_peak_cmd)
        self.lf.average_f.set_data_sample_callback(cmd=self._conn_cb.data_sample_cmd)
        self.lf.average_f.set_spectrum_average_callback(cmd=self._conn_cb.spectrum_average_cmd)
        """ Set command frame callback """
        self.cmd_f.set_entry_callback(cmd=self._conn_cb.command_box_cmd)
        """ Set main frame connection page callback """
        self.mf.connection_p.top_left_f.set_btn_callback(cmd=self._conn_cb.conn_test_cmd)
        self.mf.connection_p.set_conn_modify_ip_callback(cmd=self._conn_cb.conn_modify_ip_cmd)
        """ Set main frame initial page callback """
        self.mf.init_p.set_get_all_probes_info_callback(cmd=self._conn_cb.get_all_probes_info_cmd)
        """ Set main frame focus page callback """
        self.mf.focus_p.set_focus_set_callback(cmd=self._conn_cb.focus_set_button_cmd)
        self.mf.focus_p.set_focus_p_spectrum_button_callback(cmd=self._conn_cb.focus_spectrum_button_cmd)
        self.mf.focus_p.set_focus_p_channel_entry_callback(cmd=self._conn_cb.focus_spectrum_channel_entry_cmd)
        self.mf.focus_p.set_update_spectrum_callback(cmd=self._conn_cb.update_focus_p_spectrum_cmd)
        self.mf.focus_p.set_multichannel_profile_view_btn_callback(cmd=self._conn_cb.multichannel_profile_view_button_cmd)
        self.mf.focus_p.set_update_multichannel_profile_view_callback(cmd=self._conn_cb.update_multichannel_prof_view)
        """ Set main frame trigger test page callback """
        self.mf.trigger_test_p.right_f.set_tt_trig_mode_sel_callback(cmd=self._conn_cb.trig_test_mode_select_cmd)
        self.mf.trigger_test_p.right_f.set_tt_trig_on_return_callback(cmd=self._conn_cb.tt_trig_on_return_cmd)
        self.mf.trigger_test_p.right_f.set_axis_sel_callback(cmd=self._conn_cb.tt_axis_sel_cmd)
        self.mf.trigger_test_p.right_f.set_software_trig_callback(cmd=self._conn_cb.software_trig_cmd)
        self.mf.trigger_test_p.right_f.set_use_encoder_trig_callback(cmd=self._conn_cb.use_encoder_trig_cmd)
        self.mf.trigger_test_p.right_f.set_endless_trig_callback(cmd=self._conn_cb.endless_trig_cmd)
        self.mf.trigger_test_p.right_f.set_start_pos_callback(cmd=self._conn_cb.start_pos_cmd)
        self.mf.trigger_test_p.right_f.set_interval_callback(cmd=self._conn_cb.interval_cmd)
        self.mf.trigger_test_p.right_f.set_stop_pos_callback(cmd=self._conn_cb.stop_pos_cmd)
        self.mf.trigger_test_p.right_f.set_set_trig_pos_callback(cmd=self._conn_cb.tt_set_trig_pos_cmd)
        self.mf.trigger_test_p.set_order_encoder_callback(cmd=self._conn_cb.order_encoder_cmd)
        self.mf.trigger_test_p.set_check_trigger_callback(cmd=self._conn_cb.check_trigger_lost_cmd)
        """ Set main frame trigger scan page callback """
        self.mf.trigger_scan_p.set_tc_trig_mode_sel_callback(cmd=self._conn_cb.trig_scan_mode_select_cmd)
        self.mf.trigger_scan_p.set_tc_axis_select_callback(cmd=self._conn_cb.trig_scan_axis_sel_cmd)
        self.mf.trigger_scan_p.set_tc_en_start_pos_callback(cmd=self._conn_cb.trig_scan_en_start_pos_cmd)
        self.mf.trigger_scan_p.set_tc_en_stop_pos_callback(cmd=self._conn_cb.trig_scan_en_stop_pos_cmd)
        self.mf.trigger_scan_p.set_tc_en_interval_callback(cmd=self._conn_cb.trig_scan_en_interval_cmd)
        self.mf.trigger_scan_p.set_tc_trig_on_return_callback(cmd=self._conn_cb.trig_scan_trig_on_return_cmd)
        self.mf.trigger_scan_p.set_tc_trig_pos_callback(cmd=self._conn_cb.trig_scan_set_trig_pos_cmd)
        self.mf.trigger_scan_p.set_reset_ctn_callback(cmd=self._conn_cb.trig_scan_reset_ctn_cmd)
        self.mf.trigger_scan_p.set_tc_start_scan_callback(cmd=self._conn_cb.trig_scan_start_scan_cmd)
        self.mf.trigger_scan_p.set_tc_stop_scan_callback(cmd=self._conn_cb.trig_scan_stop_scan_cmd)
        self.mf.trigger_scan_p.set_tc_save_asc_callback(cmd=self._conn_cb.trig_scan_save_data_cmd)
        self.mf.trigger_scan_p.set_tc_selected_peak_signal_callback(cmd=self._conn_cb.trig_scan_select_signal_cmd)
        """ Set main frame multi-layer page callback """
        self.mf.multi_layer_setting_p.set_multilayer_spectrum_button_callback(
            cmd=self._conn_cb.multilayer_spectrum_button_cmd)
        self.mf.multi_layer_setting_p.set_multilayer_update_spectrum_callback(
            cmd=self._conn_cb.update_multilayer_p_spectrum_cmd)
        self.mf.multi_layer_setting_p.set_multilayer_channel_entry_callback(
            cmd=self._conn_cb.multilayer_spectrum_channel_entry_cmd)

    def clear_function_callback(self) -> None:
        """ Clear callback functions of the GUI class """
        """ Clear top frame callback """
        self.tf.output_signal_f.clear_entry_callback()
        self.tf.sample_rate_led_f.clear_shz_entry_callback()
        self.tf.sample_rate_led_f.clear_lai_entry_callback()
        self.tf.threshold_f.clear_entry_callback()
        self.tf.focus_f.clear_focus_callback()
        self.tf.device_data_flow_switch_f.set_flow_switch_sel_callback(cmd=None)

        """ Clear left frame callback """
        self.lf.dark_ref_f.set_dark_callback(cmd=None)
        self.lf.dark_ref_f.set_fast_dark_callback(cmd=None)
        self.lf.probe_sel_f.clear_probe_select_callback()
        self.lf.multilayer_stn_f.set_number_of_peak_callback(cmd=None)
        self.lf.average_f.set_data_sample_callback(cmd=None)
        self.lf.average_f.set_spectrum_average_callback(cmd=None)

        """ Clear command frame callback """
        self.cmd_f.clear_entry_callback()

        """ Clear main frame connection page callback """
        self.mf.connection_p.top_left_f.clear_btn_callback()
        self.mf.connection_p.set_conn_modify_ip_callback(cmd=None)
        """ Clear main frame initial page callback """
        self.mf.init_p.set_get_all_probes_info_callback(cmd=None)
        """ Clear main frame focus page callback """
        self.mf.focus_p.set_focus_set_callback(cmd=None)
        self.mf.focus_p.set_focus_p_spectrum_button_callback(cmd=None)
        self.mf.focus_p.set_focus_p_channel_entry_callback(cmd=None)
        self.mf.focus_p.set_update_spectrum_callback(cmd=None)
        self.mf.focus_p.set_multichannel_profile_view_btn_callback(cmd=None)
        self.mf.focus_p.set_update_multichannel_profile_view_callback(cmd=None)
        """ Clear main frame trigger test page callback """
        self.mf.trigger_test_p.right_f.clear_software_trig_callback()
        self.mf.trigger_test_p.right_f.clear_use_encoder_trig_callback()
        self.mf.trigger_test_p.right_f.clear_endless_trig_callback()
        self.mf.trigger_test_p.right_f.clear_start_pos_callback()
        self.mf.trigger_test_p.right_f.clear_interval_callback()
        self.mf.trigger_test_p.right_f.clear_stop_pos_callback()
        self.mf.trigger_test_p.right_f.clear_set_trig_pos_callback()
        self.mf.trigger_test_p.clear_order_encoder_callback()
        self.mf.trigger_test_p.clear_update_callback()
        self.mf.trigger_test_p.clear_check_trigger_callback()

        """ Clear main frame trigger scan page callback """
        self.mf.trigger_scan_p.top_left_f.first_r_f.clear_update_callback()
        self.mf.trigger_scan_p.set_tc_start_scan_callback(cmd=None)
        self.mf.trigger_scan_p.set_tc_stop_scan_callback(cmd=None)

        """ Clear main frame multi-layer page callback """
        self.mf.multi_layer_setting_p.set_multilayer_spectrum_button_callback(cmd=None)
        self.mf.multi_layer_setting_p.set_multilayer_update_spectrum_callback(cmd=None)
        self.mf.multi_layer_setting_p.set_multilayer_channel_entry_callback(cmd=None)

    def conn_callback(self, state: int) -> None:
        """
        :param state: 1: connection success
                      0: connection failed
                      -1: IP is changed, do disconnect
        """
        if state == 1:
            self.lf.conn_f.disable_ip_entry()
            self.lf.conn_f.disable_auto_button()
            self.lf.conn_f.close_conn_win()
            self.lf.conn_f.set_btn_connected()
            self.conn_init_gui()
            self.set_focus_updates()
            self.set_trigger_test_callback_updates()
            self.set_trigger_scan_callback_updates()
        elif state == 0:
            self.lf.conn_f.enable_ip_entry()
            self.lf.conn_f.conn_win.error_window()
        else:
            self.disconnect()
            self.lf.conn_f.set_btn_disconnected()

    def conn_init_gui(self) -> None:
        """ IP """
        self.mf.connection_p.set_conn_page_ip(self.lf.conn_f.get_ip())

        """ Signal IDs"""
        self.tf.output_signal_f.set_output_signal(', '.join(map(str, self._conn_prc.conf['SODX'])))

        """ Data Flow """
        self.tf.device_data_flow_switch_f.set_data_flow_option_value(self.tf.device_data_flow_switch_f.STA)
        self._conn_cb.tf_flow_switch_select_cmd()

        """ Sample Rates """
        shz = round(self._conn_prc.conf['SHZ'])
        self.tf.sample_rate_led_f.set_tf_sample_rate(shz)
        # self.mf.focus_p.set_focus_freq(shz)

        """ Lamp Intensity """
        lai = round(self._conn_prc.conf['LAI'], 5)
        self.tf.sample_rate_led_f.set_tf_led(lai)
        # self.mf.focus_p.set_focus_led(lai)

        """ Threshold """
        thr = round(self._conn_prc.conf['THR'])
        self.tf.threshold_f.set_threshold(thr)
        self.mf.multi_layer_setting_p.top_f.set_mf_peak_threshold(thr)

        """ Probe List """
        if self._conn_prc.probe_list is not []:
            probe_list = ['{}: 0-{}; SNr: {}'.format(i['Index'], i['Full Scale'], i['SN'])
                          for i in self._conn_prc.probe_list]
            self.lf.probe_sel_f.set_probe_list(probe_list)

        """ Selected Probe """
        self.lf.probe_sel_f.set_probe(self._conn_prc.conf['SEN'])
        self.lf.probe_sel_f.set_full_scale(' ' + str(self._conn_prc.conf['SCA']))
        self.mf.focus_p.update_multichannel_profile_view_distance_y_lim(0, int(self._conn_prc.conf['SCA'] * 1.1))
        if self._conn_prc.probe_list[self._conn_prc.conf['SEN']]['Pitch']:
            pitch = self._conn_prc.probe_list[self._conn_prc.conf['SEN']]['Pitch'].replace('um', '').strip()
            self.mf.trigger_scan_p.set_dy_value(pitch)

        """ Number of peaks """
        self.lf.multilayer_stn_f.set_lf_number_of_peak(self._conn_prc.conf['NOP'])
        self.mf.multi_layer_setting_p.top_f.set_mf_number_of_peak(self._conn_prc.conf['NOP'])

        """ Average """
        self.lf.average_f.set_data_sample(self._conn_prc.conf['AVD'])
        self.mf.init_p.bottom_right_f.set_avd(self._conn_prc.conf['AVD'])
        self.lf.average_f.set_spectrum_average(self._conn_prc.conf['AVS'])
        self.mf.init_p.bottom_right_f.set_avs(self._conn_prc.conf['AVS'])

        """ Trigger Mode """
        self.tf.device_measurement_mode_f.set_tf_trig_mode_value(0)
        self._conn_cb.tf_trig_mode_select_cmd()
        self.mf.trigger_test_p.clear_trigger_lost_info()

        """ Spectrum """
        self.mf.focus_p.set_focus_spectrum_btn_normal()
        self.mf.focus_p.set_focus_spectrum_channel('0')
        self.mf.multi_layer_setting_p.set_multilayer_spectrum_btn_normal()
        self.mf.multi_layer_setting_p.set_multilayer_spectrum_channel('0')

    def disconnect(self) -> None:
        self._conn_prc.async_cmd.disconn()
        self.lf.conn_f.enable_ip_entry()
        self.lf.conn_f.enable_auto_button()
        self._conn_prc.set_connection_off_flags()
        self.clear_function_callback()
        self.set_app_callback()
        self.clear_gui_data()
        self.clear_gui_timer()
        self.set_connection_off_gui()

    def clear_gui_data(self):
        self.set_device_type('')
        self.lf.probe_sel_f.clear_probe_list()
        self.lf.probe_sel_f.clear_probe()
        self.lf.probe_sel_f.clear_full_scale_string()
        self.lf.multilayer_stn_f.set_lf_number_of_peak('')
        self.lf.average_f.clear_data_sample()
        self.lf.average_f.clear_spectrum_average()
        self.tf.sample_rate_led_f.clear_tf_sample_rate()
        self.tf.sample_rate_led_f.clear_tf_led()
        self.tf.threshold_f.clear_threshold()
        self.mf.init_p.top_left_f.clear_sen()
        self.mf.init_p.top_left_f.clear_shz()
        self.mf.init_p.top_left_f.clear_lai()
        self.mf.init_p.top_left_f.clear_dark_type()
        self.mf.init_p.init_probe_info_textbox()
        self.mf.init_p.bottom_right_f.clear_avd()
        self.mf.init_p.bottom_right_f.clear_avs()
        self.mf.focus_p.set_focus_move_str(direction=-2)
        self.mf.focus_p.set_focus_spectrum_btn_normal()
        self.mf.focus_p.set_multichannel_profile_view_btn_normal()
        self.mf.trigger_test_p.clear_encoder_x_value()
        self.mf.trigger_test_p.clear_encoder_y_value()
        self.mf.trigger_test_p.clear_encoder_z_value()
        self.mf.trigger_test_p.clear_sample_counter_value()
        self.mf.trigger_test_p.clear_trigger_happened()
        self.mf.trigger_test_p.clear_trigger_count()
        self.mf.trigger_test_p.clear_trigger_lost_info()
        self.mf.trigger_scan_p.tc_set_peak_id_options([])
        self.mf.trigger_scan_p.tc_set_peak_id('')
        self.mf.trigger_scan_p.set_tc_start_scan_btn(False)
        self.mf.trigger_scan_p.tc_start_scan_btn_stat(False)
        self.mf.multi_layer_setting_p.top_f.clear_mf_number_of_peak()
        self.mf.multi_layer_setting_p.top_f.clear_mf_peak_threshold()
        self.mf.multi_layer_setting_p.set_multilayer_spectrum_btn_normal()
        self.mf.multi_layer_setting_p.set_multilayer_spectrum_channel('')

    def clear_gui_timer(self):
        self.mf.trigger_test_p.stop_update_data()

    def set_connection_off_gui(self):
        self.mf.connection_p.top_left_f.set_btn_normal()

    def set_focus_updates(self) -> None:
        self.tf.focus_f.set_focus_callback(cmd=self._conn_cb.update_focus_distance)
        self.tf.focus_f.update_focus()

    def set_trigger_test_callback_updates(self) -> None:
        self.mf.trigger_test_p.set_tt_update_callback(cmd=self._conn_cb.update_trigger_test)
        self.mf.trigger_test_p.update_data()

    def set_trigger_scan_callback_updates(self) -> None:
        self.mf.trigger_scan_p.top_left_f.first_r_f.set_tc_update_callback(cmd=self._conn_cb.update_trigger_scan)
        self.mf.trigger_scan_p.start_auto_update_sample_counter()


class ConnProcess(Thread):
    def __init__(self, master: App, ip: str = '', device_type: DeviceType = DeviceType.CHR_MULTI_CHANNEL,
                 conn_callback: Callable = None,
                 update_freq: int = 20):
        super().__init__()
        self.daemon = True
        self._master = master
        self._ip = ip
        self._device_type = device_type
        self.sync_conn = None
        self.async_cmd = AsyncCommand(master, cmd_rsp_handle=self.cmd_rsp_handle)
        self.freq = update_freq
        self.data_acq = DataAcquisition()
        self.conn_callback = conn_callback

        """ Init samples threads  """
        self._samples_queue = Queue()
        self._conn_samples_thread = ConnSamplesThread(master=master, queue=self._samples_queue, update_freq=4)
        self._distance_1_queue = Queue()
        self._conn_distance_1_thread = ConnDistance1Thread(master=master, queue=self._distance_1_queue, update_freq=4)
        self._trigger_lost_queue = Queue()
        self._trigger_lost_verify_thread = None
        self._scan_thread = None

        """ Init data structures """
        self.conf = {
            'SHZ': 0,
            'LAI': 0,
            'THR': 0,
            'SEN': 0,
            'SCA': 0,
            'NOP': 0,
            'AVD': 0,
            'AVS': 0,
            'NCH': 0,
            'SODX': []
        }
        self.default_header = {
            "File Format": '',
            "x-pixels": 0,
            "y-pixels": 0,
            "x-length": 0,
            "y-length": 0,
            "x-offset": 0,
            "y-offset": 0,
            "z-unit": '',
            "scanspeed": 0,
            "forcecurve": 0,
            "voidpixels": 0,
            "description": ''
        }

        self.probe_list = []
        self.signal_ids = []

        """ Connection Event """
        self._conn_on = Event()

        """ Data Event """
        self.samples_ready = Event()
        self.samples_ready.clear()

        self.spectrum_channel = 0
        self.spectrum_is_on = False
        self.multichannel_view_is_on = False
        self.last_sample_cnt = None
        self.last_distance_1_int16_ch1 = None
        self.last_distance_1_ch1 = None
        self.last_intensity_ch1 = None
        self.last_distance_1 = None
        self.last_intensity_1 = None
        self.encoder_x = None
        self.encoder_y = None
        self.encoder_z = None
        self.exposure_flags = None
        self.spectrum_data = None

    def run(self):
        try:
            with connection_from_params(addr=self._ip, device_type=self._device_type) as self.sync_conn:
                log.info('Connection ON')
                self.init_threads()
                self.async_cmd.conn(ip=self._ip, device_type=self._device_type)
                self._conn_on.set()
                self.sync_exec('SODX 83 16640 16641')
                self.get_configs()
                self.flush_connection_buffer()
                self.init_data_acq_thread()
                self.conn_callback(1)
                while self._conn_on.is_set():
                    self._update_samples()
                    self._download_spectrum()
                    self.update_focus_move()
                    self.update_intensity()
                    sleep(1 / self.freq)
        except Exception or APIException as err:
            self.async_cmd.disconn()
            self.samples_ready.clear()
            self.set_connection_off_flags()
            self.conn_callback(0)
            if err.args[0]:
                log.warning('Connection FAILED: ' + err.args[0])
            elif err.error_string[0]:
                log.warning('Connection FAILED: ' + err.error_string[0])
            log.exception('Connection FAILED')
        self.clear_queues()
        log.info('ConnProcess (Thread) Closed')

    def _update_samples(self):
        """ Get samples from the data acq thread when the new samples is ready. """
        if not self.data_acq.samples_collected.is_set():
            self.samples_ready.clear()
            self.last_sample_cnt = self.data_acq.get_last_sample_count()
            self.last_distance_1_int16_ch1 = self.data_acq.get_last_distance_1_int16_ch1()
            self.last_distance_1_ch1 = self.data_acq.get_last_distance_1_ch1()
            self.last_intensity_ch1 = self.data_acq.get_last_intensity_ch1()
            self.last_distance_1 = self.data_acq.get_last_distance_1()
            self.last_intensity_1 = self.data_acq.get_last_intensity_1()
            self.encoder_x = self.data_acq.get_encoder_x()
            self.encoder_y = self.data_acq.get_encoder_y()
            self.encoder_z = self.data_acq.get_encoder_z()
            self.exposure_flags = self.data_acq.get_exposure_flags()
            try:
                sample_cnt = self.data_acq.get_sample_count()
                distance_1_int16 = self.data_acq.get_distance_1_int16()
                distance_1_int16_ch1 = None
                if distance_1_int16 is not None:
                    if isinstance(distance_1_int16[0], Iterable):
                        distance_1_int16_ch1 = [i[0] for i in distance_1_int16] if distance_1_int16 is not None \
                            else None
                    else:
                        distance_1_int16_ch1 = [i for i in distance_1_int16] if distance_1_int16 is not None else None
                distance_1 = self.data_acq.get_distance_1()
                # intensity = self.data_acq.get_intensity()

                """ Main Frame - Connection - Sample Thread """
                if (sample_cnt is not None) and self._conn_samples_thread.is_resume():
                    try:
                        self._samples_queue.put_nowait(sample_cnt)
                    except Full:
                        log.exception('Samples Queue is full')

                """ Main Frame - Connection - Distance 1 Thread """
                if (distance_1 is not None) and self._conn_distance_1_thread.is_resume():
                    if isinstance(distance_1[0], Iterable):
                        distance_1_ch1 = np.array([i[0] for i in distance_1])
                    else:
                        distance_1_ch1 = np.array([i for i in distance_1])
                    try:
                        self._distance_1_queue.put_nowait(distance_1_ch1)
                        # log.info('[ConnProc] Put distance to Queue')
                    except Full:
                        log.exception('Distance 1 Queue is full')

                """ Main Frame - Trigger Test - Trigger Lost Verify Thread """
                x_state = self.encoder_x is not None
                y_state = self.encoder_y is not None
                z_state = self.encoder_z is not None
                if self._trigger_lost_verify_thread.trig_verify_thread_on() and (x_state or y_state or z_state):
                    try:
                        self._trigger_lost_queue.put_nowait([sample_cnt, self.encoder_x, self.encoder_y,
                                                             self.encoder_z, self.exposure_flags, distance_1_int16_ch1])
                    except Full:
                        log.exception('Trigger Lost Queue is full')

            except ValueError:
                log.exception('_update_samples ValueError')
            finally:
                self.data_acq.samples_collected.set()
                # log.info('[ConnProc] Set data_acq samples_collected.')
                self.samples_ready.set()

    def _download_spectrum(self):
        if self.spectrum_is_on:
            current_tab_index = self._master.mf.notebook.index(self._master.mf.notebook.select())
            if current_tab_index == 3:
                channel_str = self._master.mf.focus_p.get_focus_spectrum_channel()
            else:
                channel_str = self._master.mf.multi_layer_setting_p.get_multilayer_spectrum_channel()
            channel = 0 if channel_str == '' else int(channel_str)
            resp = self.sync_conn.download_spectrum(SpectrumType.CONFOCAL, channel)
            if resp.error_code != 0:
                raise APIException(self.sync_conn.dll_handle(), resp.error_code)
            par = resp.args[resp.param_count - 1]
            self.spectrum_data = np.frombuffer(par, dtype=np.short)

    def update_focus_move(self):
        current_tab_index = self._master.mf.notebook.index(self._master.mf.notebook.select())
        if current_tab_index == 3:
            if self.last_distance_1_ch1 is not None:
                distance = int(self.last_distance_1_ch1)
                scale = self.conf['SCA']
                hi_lim = scale / 2 * 1.2
                lo_lim = scale / 2 * 0.8
                if lo_lim <= distance <= hi_lim:
                    self._master.mf.focus_p.set_focus_move_str(direction=0)
                elif distance == 0:
                    self._master.mf.focus_p.set_focus_move_str(direction=-2)
                elif distance > hi_lim:
                    self._master.mf.focus_p.set_focus_move_str(direction=-1, distance=int(distance - scale / 2))
                elif distance < lo_lim:
                    self._master.mf.focus_p.set_focus_move_str(direction=1, distance=int(scale / 2 - distance))

    def update_intensity(self):
        if self.last_intensity_ch1 is not None:
            self._master.tf.intensity_f.set_intensity_value(str(self.last_intensity_ch1))
            self._master.tf.intensity_f.set_intensity_prog_bar_value(str(self.last_intensity_ch1))

    def sync_exec(self, cmd_str: str, args=None) -> Response:
        if args is None:
            args = []
        if self.conn_on():
            cmd_list = cmd_str.split(' ')
            txt = '[Sensor] <<$'
            rsp = False
            try:
                q_str = ''
                if '?' in cmd_str:
                    q_str = '?'
                rsp = self.sync_conn.send_command_string(cmd_str)
                if rsp and (rsp.error_code == 0):
                    rsp_args = rsp.args if len(rsp.args) > 0 else None
                    if type(rsp_args) == list:
                        if type(rsp_args[0]) == list:
                            arg_str = '; '.join([str(i) for i in rsp_args[0]])
                        else:
                            arg_str = '; '.join([str(i) for i in rsp_args])
                    elif type(rsp_args) == float:
                        arg_str = str(round(rsp_args, 5))
                    elif not rsp_args:
                        arg_str = ''
                    else:
                        arg_str = str(rsp_args)
                    txt += (cmd_list[0] + q_str + arg_str).replace('\00', '')
                else:
                    txt += '{}\n<<Error in CMD!'.format(cmd_str)
            except Exception as e:
                txt += '[App Info] {}\n<<Error in CMD!'.format(cmd_str)
            self._master.cmd_f.insert_textbox(txt)

            if 'SODX' in str(rsp) and rsp.error_code == 0:
                self.signal_ids = rsp.args[0]
                signal_id_str = ", ".join(str(i) for i in rsp.args[0])
                self._master.tf.output_signal_f.set_output_signal(signal_id_str)

            _mapping_dict = {
                16640: 'Distance 1',
                16641: 'Intensity 1'
            }
            filtered_prof_view_list = [_mapping_dict[item] for item in self.signal_ids if item in _mapping_dict]
            self._master.mf.focus_p.set_multichannel_profile_view_id_list(filtered_prof_view_list)
            return rsp

    def async_exec(self, cmd_str: str, args: Args = None, gui_update=False) -> Rsp:
        if self._conn_on.is_set():
            try:
                self.async_cmd.gui_update = gui_update
                cmd_list = cmd_str.split(' ')
                cmd = cmd_list[0]
                if '?' in cmd_str:
                    self.async_cmd.query_cmd = cmd
                    mark_index = cmd_list.index('?')
                    if mark_index == 1:
                        rsp = self.async_cmd.async_conn.query(cmd)
                    elif mark_index > 1:
                        if 'enum' in cmd_str:
                            """ for the case of $SENX enum ? """
                            rsp = self.async_cmd.async_conn.send_command_string(cmd_str)
                        else:
                            rsp = self.async_cmd.async_conn.query(cmd,
                                                                  self.arg_str_to_int_float(cmd_list[1:mark_index]))
                    else:
                        return False
                elif args:
                    rsp = self.async_cmd.async_conn.exec(cmd_str, self.arg_str_to_int_float(args))
                else:
                    if len(cmd_list) > 1:
                        self.async_cmd_filter(cmd_str, self.arg_str_to_int_float(cmd_list[1:]))
                        rsp = self.async_cmd.async_conn.exec(cmd, self.arg_str_to_int_float(cmd_list[1:]))
                    else:
                        rsp = self.async_cmd.async_conn.exec(cmd_str)
            except APIException:
                return False
            except ValueError:
                rsp = None
            if rsp is None:
                self._master.cmd_f.insert_textbox('[App Info] <<Error in CMD!')
            return rsp

    def conn_prc_disconn(self):
        self.samples_ready.clear()
        self.set_connection_off_flags()
        self.conn_callback(0)

    def async_cmd_filter(self, cmd_str, arg_list):
        if 'ETR' in cmd_str:
            if arg_list[0] in [0, 1, 2, 4, 5, 7]:
                self.async_cmd.etr_cmds_index.append(arg_list[0])

    def init_threads(self):
        self._trigger_lost_verify_thread = TrigLostVerifyThread(master=self._master, queue=self._trigger_lost_queue,
                                                                update_freq=10)
        self._scan_thread = ScanThread(master=self._master, conn=self.sync_conn)

    def conn_on(self):
        return self._conn_on.is_set()

    def get_configs(self):
        """ Get probe list from sensor """
        self.probe_list = []
        rsp = self.sync_conn.query('SENX', 'enum', '?')
        rsp_string_list = [i[:-1] for i in rsp.args if i[3:6].lower() == 'snr']
        for i in rsp_string_list:
            string_list = i.split(',')
            index = string_list[0]
            sn = string_list[1].replace(' SNr:', '')
            full_scale = string_list[2].replace(' Range:', '')
            pitch = string_list[3].replace(' Pitch:', '') if len(string_list) >= 4 else None
            self.probe_list.append({'Index': index,
                                    'SN': sn,
                                    'Full Scale': full_scale,
                                    'Pitch': pitch})

        """ Get signal ID from sensor """
        self.conf['SODX'] = self.sync_conn.query('SODX').args[0]

        """ Get conf list from sensor """
        self.conf['SHZ'] = self.sync_conn.query('SHZ').args[0]
        self.conf['LAI'] = self.sync_conn.query('LAI').args[0]
        self.conf['THR'] = self.sync_conn.query('THR').args[0]
        self.conf['SEN'] = self.sync_conn.query('SEN').args[0]
        self.conf['SCA'] = self.sync_conn.query('SCA').args[0]
        self.conf['NOP'] = self.sync_conn.query('NOP').args[0]
        self.conf['AVD'] = self.sync_conn.query('AVD').args[0]
        self.conf['AVS'] = self.sync_conn.query('AVS').args[0]
        self.conf['NCH'] = get_device_channel_count(self.sync_conn.dll_handle(), self.sync_conn.conn_handle)
        dev_str = [i for i in self.sync_conn.query('PRSN').args[0].split(' ') if 'devicetype' in i][0]
        self.conf['PRSN'] = dev_str[dev_str.find('devicetype') + 11:]
        self._master.set_device_type(self.conf['PRSN'])

        # Set the saturation intensity level value to Trigger Scan Frame
        if self.conf['PRSN'] == 'CLS_192':
            sat_lvl = config.get('Intensity Saturation Level', 'CLS')
            self._master.mf.trigger_scan_p.set_tc_saturation_level(sat_lvl)
        elif self.conf['PRSN'] == 'CLS2_1200':
            sat_lvl = config.get('Intensity Saturation Level', 'CLS2')
            self._master.mf.trigger_scan_p.set_tc_saturation_level(sat_lvl)
            # self._master.mf.focus_p.update_multichannel_profile_view_distance_y_lim(-10, 1300)
        else:
            self._master.mf.trigger_scan_p.set_tc_saturation_level('4095')

        if 'CLS' in self.conf['PRSN']:
            self._master.mf.trigger_scan_p.tc_start_scan_btn_stat(True)
        else:
            self._master.mf.trigger_scan_p.tc_start_scan_btn_stat(False)

    def init_data_acq_thread(self):
        self.data_acq = DataAcquisition(conn=self.sync_conn)
        self.data_acq.set_full_scale(self.conf['SCA'])
        self.data_acq.set_get_next_sample_count(int(self.conf['SHZ'] / 2))
        self.data_acq.start_reading()
        self.data_acq.start()

    def clear_queues(self):
        self._samples_queue.queue.clear()
        self._distance_1_queue.queue.clear()
        self._trigger_lost_queue.queue.clear()

    """ Main Frame - Connection - Sample Counter plot Thread """

    # region
    def start_conn_samples_thread(self):
        self._conn_samples_thread.set_thread_on()
        self._conn_samples_thread.start()

    def pause_conn_samples(self):
        self._conn_samples_thread.pause_thread()

    def resume_conn_samples(self):
        self._conn_samples_thread.resume_thread()

    def stop_conn_samples_thread(self):
        self._conn_samples_thread.clear_thread_on()

    # endregion

    """ Main Frame - Connection - Distance 1 plot Thread """

    # region
    def start_conn_distance_1_thread(self):
        self._conn_distance_1_thread.set_thread_on()
        self._conn_distance_1_thread.set_full_scale(self.conf['SCA'])
        self._conn_distance_1_thread.start()

    def pause_conn_distance_1(self):
        self._conn_distance_1_thread.pause_thread()

    def resume_conn_distance_1(self):
        self._conn_distance_1_thread.resume_thread()

    def stop_conn_distance_1_thread(self):
        self._conn_distance_1_thread.clear_thread_on()

    # endregion

    """ Main Frame - Trigger Test - Trigger Lost Verify Thread """

    # region
    def start_trigger_lost_verify_thread(self):
        self._trigger_lost_queue = Queue()
        self._trigger_lost_verify_thread = TrigLostVerifyThread(master=self._master, queue=self._trigger_lost_queue,
                                                                update_freq=10)
        self.sync_exec('SODX 65 66 67 76 83 16640 16641')
        self._trigger_lost_verify_thread.start()

    def stop_trigger_lost_verify_thread(self):
        if self._trigger_lost_verify_thread is not None:
            self._trigger_lost_verify_thread.user_cancel()
            self._trigger_lost_verify_thread.clear_thread_on()

    # endregion

    """ Main Frame - Trigger Scan - Scan Thread """

    # region
    def start_scan_thread(self):
        log.info('Start Trigger Scan')
        self.data_acq.stop_reading()
        self.sync_exec('STO')
        self._master.tf.device_data_flow_switch_f.set_data_flow_option_value(1)  # set data flow switch to STO
        timeout = 5
        start_time = time.time()
        while self.data_acq.thread_is_on():
            if time.time() - start_time > timeout:
                log.error('self.data_acq.thread_is_on(): ', self.data_acq.thread_is_on())
                log.error('Timeout: Data acquisition thread did not finish.')
                break
            sleep(0.05)
        self._scan_thread = ScanThread(master=self._master, conn=self.sync_conn, close_cmd=self.init_data_acq_thread,
                                       sync_exec=self.sync_exec)

        # 生成signal ID 字串 for SODX multilayer掃描使用
        nop = int(self._master.lf.multilayer_stn_f.get_lf_number_of_peak())
        if nop > 4:
            nop = 4
            self.sync_exec('NOP {}'.format(nop))
        ids = []
        for i in range(nop):
            ids.extend([str(16640 + i * 8), str(16641 + i * 8)])
        peak_signal_ids = ' '.join(ids)

        if self._master.mf.trigger_scan_p.get_tc_trig_mode_value() == 2:
            sel_axis = self._master.mf.trigger_scan_p.get_tc_axis()
            encoder_ids = {'x': '65', 'y': '66', 'z': '67', 'u': '68', 'v': '69'}
            encoder_id = encoder_ids.get(sel_axis, '65')
            self._scan_thread.encoder_id = encoder_id
            self.sync_exec('SODX {} 83 {}'.format(encoder_id, peak_signal_ids))
            self.sync_exec('ETR 0 ' + str(self._master.mf.trigger_scan_p.get_tc_en_start_pos()))
            self.sync_exec('ETR 2 ' + str(self._master.mf.trigger_scan_p.get_tc_en_interval()))
            self.sync_exec('ETR 1 ' + str(self._master.mf.trigger_scan_p.get_tc_en_stop_pos()))
        else:
            self.sync_exec('SODX 83 {}'.format(peak_signal_ids))
        self._master.mf.trigger_scan_p.stop_auto_update_sample_counter()
        self._scan_thread.start()

    def stop_scan_thread(self):
        if self._scan_thread is not None:
            self._scan_thread.stop_scan()

    def plot_selected_id(self):
        selected_str = self._master.mf.trigger_scan_p.tc_get_peak_id()
        if selected_str == '16641 (highlight saturation)':
            selected_id = 'sat'
        else:
            selected_id = selected_str.split()[0]
        self._master.mf.trigger_scan_p.tc_set_plot_unit(self._scan_thread.id_to_units[selected_id])
        self._scan_thread.plot_data_to_gui(selected_id)

    def get_scan_data(self, id_str: str) -> numpy.array:
        return self._scan_thread.get_data(id_str)

    def get_scan_peak_ids(self) -> list:
        return self._scan_thread.get_peak_ids()

    def scan_data_is_ready(self):
        if self._scan_thread is not None:
            is_ready = self._scan_thread.data_is_ready()
        else:
            is_ready = False
        return is_ready

    def get_scan_data_ch_cnt(self) -> int:
        return self._scan_thread.get_ch_cnt()

    def get_scan_data_ln_cnt(self) -> int:
        return self._scan_thread.get_ln_cnt()

    def get_scan_data_dx(self) -> float:
        return self._scan_thread.get_dx()

    def get_scan_data_dy(self) -> float:
        return self._scan_thread.get_dy()

    def get_scan_data_line_sample_cnt(self) -> int:
        return self._scan_thread.get_line_sample_cnt()

    # endregion

    """ Command Frame """

    # region
    def cmd_rsp_handle(self, cmd_str, arg):
        if cmd_str == 'SHZ':
            self.data_acq.set_get_next_sample_count(cnt=int(arg / 2))

    # endregion

    def get_connection_on_flag(self):
        return self._conn_on.is_set()

    def set_connection_off_flags(self):
        self.samples_ready.clear()
        self.data_acq.stop_reading()
        self.stop_conn_samples_thread()
        self.stop_conn_distance_1_thread()
        self.stop_trigger_lost_verify_thread()
        self.stop_scan_thread()
        self._conn_on.clear()

    # region
    @staticmethod
    def arg_str_to_int_float(str_list):
        if str_list[0].isdigit():
            cmd_args = [int(i) for i in str_list]
        else:
            cmd_args = [float(i) for i in str_list]
        return cmd_args

    def flush_connection_buffer(self):
        self.sync_conn.flush_connection_buffer()
    # endregion


class AppCallback(object):
    def __init__(self, master: App, app_prc: AppProcess) -> None:
        self._master = master
        self.app_prc = app_prc
        self.tf_ctn = self._master.tf.device_measurement_mode_f.CTN
        self.tf_trg = self._master.tf.device_measurement_mode_f.TRG
        self.tf_tre = self._master.tf.device_measurement_mode_f.TRE
        self.mf_tt_ctn = self._master.mf.trigger_test_p.right_f.CTN
        self.mf_tt_trg = self._master.mf.trigger_test_p.right_f.TRG
        self.mf_tt_tre = self._master.mf.trigger_test_p.right_f.TRE
        self.mf_tc_ctn = self._master.mf.trigger_scan_p.top_left_f.second_r_f.CTN
        self.mf_tc_sync = self._master.mf.trigger_scan_p.top_left_f.second_r_f.SYNC
        self.mf_tc_tre = self._master.mf.trigger_scan_p.top_left_f.second_r_f.TRE
        self.axis_map = {'x': '0', 'y': '1', 'z': '2', 'u': '3', 'v': '4'}

    def set_introduction_page_callback(self):
        self._master.mf.introduction_p.set_open_manual_callback(cmd=self.app_prc.open_manual)
        self._master.mf.introduction_p.set_open_sample_code_callback(cmd=self.app_prc.open_sample_code)
        self._master.mf.introduction_p.set_sample_code_table_callback(cmd=self.sample_code_table_cmd)
        self._master.mf.introduction_p.set_search_sample_code_callback(cmd=self.search_sample_code_cmd)
        self._master.mf.introduction_p.set_open_api_callback(cmd=self.app_prc.open_chr_dll_dir)
        self._master.mf.introduction_p.set_open_chr_explorer_callback(cmd=self.app_prc.open_chr_explorer_dir)

    def set_on_close_callback(self):
        self._master.set_on_close_callback(self.on_close_cmd)

    # region Top frame callback

    def app_sample_rate_cmd(self) -> None:
        self.tc_max_speed_cmd()

    def tf_trig_mode_select_cmd(self) -> None:
        selected_mode = self._master.tf.device_measurement_mode_f.get_tf_trig_mode_value()
        if selected_mode == self.tf_ctn:
            self._master.mf.trigger_test_p.right_f.set_tt_trig_mode_value(self.mf_tt_ctn)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_ctn)
        elif selected_mode == self.tf_trg:
            self._master.mf.trigger_test_p.right_f.set_tt_trig_mode_value(self.mf_tt_trg)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(None)
        elif selected_mode == self.tf_tre:
            self._master.mf.trigger_test_p.right_f.set_tt_trig_mode_value(self.mf_tt_tre)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_tre)

    def intensity_level_attachment_cmd(self) -> None:
        self.app_prc.open_intensity_level_attachment()

    # endregion

    # region Introduction callback

    def search_sample_code_cmd(self):
        sample_code_index = self._master.mf.introduction_p.get_search_entry().lower()
        if len(sample_code_index) > 0:
            if sample_code_index.startswith('cp'):
                section = 'SampleCode Cpp'
            elif sample_code_index.startswith('cs'):
                section = 'SampleCode Cs'
            elif sample_code_index.startswith('py'):
                section = 'SampleCode Python'
            else:
                text = '[App Info] The index should start with cp, cs or py.'.format(sample_code_index)
                self._master.cmd_f.insert_textbox(text)
                return
            try:
                sample_code_path = config.get(section, sample_code_index)
                subprocess.Popen('explorer /select,{}'.format(os.path.join(py_dir, sample_code_path)))
            except NoOptionError:
                text = '[App Info] There is no {} sample code. Please check the sample code table again.'.format(sample_code_index)
                self._master.cmd_f.insert_textbox(text)

    @staticmethod
    def sample_code_table_cmd():
        table_dir = config.get('DocPath', 'sample_code_table')
        table_path = os.path.join(py_dir, table_dir)
        subprocess.Popen([table_path], shell=True)

    # endregion

    # region Trigger Test callback

    def trig_test_mode_select_cmd(self) -> None:
        selected_mode = self._master.mf.trigger_test_p.right_f.get_tt_trig_mode_value()
        if selected_mode == self.mf_tt_ctn:
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_ctn)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_ctn)
        elif selected_mode == self.mf_tt_trg:
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_trg)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(None)
        elif selected_mode == self.mf_tt_tre:
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_tre)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_tre)

    def tt_use_encoder_trig_cmd(self):
        if self._master.mf.trigger_test_p.right_f.get_use_encoder_trig() == 1:
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_tre)
        else:
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_sync)

    def tt_trig_on_return_cmd(self) -> None:
        sel = self._master.mf.trigger_test_p.right_f.get_tt_trig_on_return()
        self._master.mf.trigger_scan_p.set_tc_trig_on_return(sel)

    def tt_axis_sel_cmd(self) -> None:
        selected_axis = self._master.mf.trigger_test_p.right_f.get_tt_axis()
        self._master.mf.trigger_scan_p.set_tc_axis(selected_axis)
        self._master.mf.trigger_scan_p.set_tc_encoder_type(selected_axis)

    # endregion

    # region Trigger Scan callback
    def tc_cal_sample_count(self) -> None:
        en_stop_pos = self._master.mf.trigger_scan_p.get_tc_en_stop_pos()
        en_start_pos = self._master.mf.trigger_scan_p.get_tc_en_start_pos()
        interval = self._master.mf.trigger_scan_p.get_tc_en_interval()
        if en_start_pos is not None and en_stop_pos is not None and interval is not None:
            self._master.mf.trigger_scan_p.set_tc_sample_count(str(int((en_stop_pos - en_start_pos) / interval + 1)))

    def tc_mode_select_cmd(self) -> None:
        selected_mode = self._master.mf.trigger_scan_p.get_tc_trig_mode_value()
        if selected_mode == self.mf_tc_ctn:
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_ctn)
            self._master.mf.trigger_test_p.right_f.set_tt_trig_mode_value(self.mf_tt_ctn)
        elif selected_mode == self.mf_tc_sync:
            self._master.mf.trigger_test_p.right_f.set_use_encoder_trig(0)
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_tre)
            self._master.mf.trigger_test_p.right_f.set_tt_trig_mode_value(self.mf_tt_tre)
            self._master.mf.trigger_test_p.right_f.tt_check_trigger_each_widgets_state()
        elif selected_mode == self.mf_tc_tre:
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_tre)
            self._master.mf.trigger_test_p.right_f.set_tt_trig_mode_value(self.mf_tt_tre)
            self._master.mf.trigger_test_p.right_f.set_use_encoder_trig(1)
            self._master.mf.trigger_test_p.right_f.tt_check_trigger_each_widgets_state()
        self._master.mf.trigger_scan_p.tc_check_trigger_each_widgets_state()

    def tc_axis_sel_cmd(self) -> None:
        selected_axis = self._master.mf.trigger_scan_p.get_tc_axis()
        self._master.mf.trigger_test_p.right_f.set_tt_axis(selected_axis)
        self._master.mf.trigger_scan_p.set_tc_encoder_type(selected_axis)

    def tc_encoder_resolution_cmd(self) -> None:
        encoder_resolution = self._master.mf.trigger_scan_p.get_encoder_resolution()
        self._master.mf.trigger_scan_p.set_encoder_resolution(str(encoder_resolution))
        dx = self._master.mf.trigger_scan_p.get_dx_value()
        if (encoder_resolution is not None) and (dx is not None) and (encoder_resolution != 0):
            interval = int(dx / encoder_resolution)
            self._master.mf.trigger_scan_p.set_tc_en_interval(interval)
        elif encoder_resolution == 0:
            self._master.mf.trigger_scan_p.set_encoder_resolution('')
        self.tc_cal_sample_count()

    def tc_en_start_pos_cmd(self) -> None:
        encoder_resolution = self._master.mf.trigger_scan_p.get_encoder_resolution()
        en_start_pos = self._master.mf.trigger_scan_p.get_tc_en_start_pos()
        if encoder_resolution and (en_start_pos is not None):
            self._master.mf.trigger_scan_p.set_tc_pos_start_pos(str(encoder_resolution * en_start_pos / 1000))
        self.tc_cal_sample_count()
        self._master.mf.trigger_test_p.right_f.set_start_pos(str(en_start_pos))

    def tc_en_stop_pos_cmd(self) -> None:
        encoder_resolution = self._master.mf.trigger_scan_p.get_encoder_resolution()
        en_stop_pos = self._master.mf.trigger_scan_p.get_tc_en_stop_pos()
        if encoder_resolution and (en_stop_pos is not None):
            self._master.mf.trigger_scan_p.set_tc_pos_stop_pos(str(encoder_resolution * en_stop_pos / 1000))
        self.tc_cal_sample_count()
        self._master.mf.trigger_test_p.right_f.set_stop_pos(str(en_stop_pos))

    def tc_en_interval_cmd(self) -> None:
        encoder_resolution = self._master.mf.trigger_scan_p.get_encoder_resolution()
        en_interval = self._master.mf.trigger_scan_p.get_tc_en_interval()
        if en_interval is not None and encoder_resolution is not None:
            self._master.mf.trigger_scan_p.set_tc_pos_interval(str(encoder_resolution * en_interval / 1000))
        self.tc_cal_sample_count()
        self._master.mf.trigger_test_p.right_f.set_interval(str(en_interval))

    def tc_pos_start_pos_cmd(self) -> None:
        encoder_resolution = self._master.mf.trigger_scan_p.get_encoder_resolution()
        pos_start_pos = self._master.mf.trigger_scan_p.get_tc_pos_start_pos()
        if encoder_resolution and (pos_start_pos is not None):
            en_start_pos = int(pos_start_pos * 1000 / encoder_resolution)
            self._master.mf.trigger_scan_p.set_tc_en_start_pos(f'{en_start_pos:,}')
        self.tc_cal_sample_count()

    def tc_pos_stop_pos_cmd(self) -> None:
        encoder_resolution = self._master.mf.trigger_scan_p.get_encoder_resolution()
        pos_stop_pos = self._master.mf.trigger_scan_p.get_tc_pos_stop_pos()
        if encoder_resolution and (pos_stop_pos is not None):
            en_stop_pos = int(pos_stop_pos * 1000 / encoder_resolution)
            self._master.mf.trigger_scan_p.set_tc_en_stop_pos(f'{en_stop_pos:,}')
            self._master.mf.trigger_test_p.right_f.set_stop_pos(str(en_stop_pos))
        pos_start_pos = self._master.mf.trigger_scan_p.get_tc_pos_start_pos()
        if (pos_start_pos is not None) and (pos_stop_pos is not None):
            self._master.mf.trigger_scan_p.set_x_scan_length(str(pos_stop_pos - pos_start_pos))
        self.tc_cal_sample_count()

    def tc_pos_interval_cmd(self) -> None:
        encoder_resolution = self._master.mf.trigger_scan_p.get_encoder_resolution()
        pos_interval = self._master.mf.trigger_scan_p.get_tc_pos_interval()
        if encoder_resolution and (pos_interval is not None):
            en_interval = int(pos_interval * 1000 / encoder_resolution)
            self._master.mf.trigger_scan_p.set_tc_en_interval(f'{en_interval:,}')
        self.tc_cal_sample_count()

    def tc_x_scan_length_cmd(self) -> None:
        x_scan_length = self._master.mf.trigger_scan_p.get_x_scan_length()
        pos_start_pos = self._master.mf.trigger_scan_p.get_tc_pos_start_pos()
        if x_scan_length and (pos_start_pos is not None):
            self._master.mf.trigger_scan_p.set_tc_pos_stop_pos(str(pos_start_pos + x_scan_length))
            self.tc_pos_stop_pos_cmd()
        self.tc_cal_sample_count()

    def tc_scan_dx_cmd(self) -> None:
        dx = self._master.mf.trigger_scan_p.get_dx_value()
        if dx is not None:
            self._master.mf.trigger_scan_p.set_tc_pos_interval(format(dx / 1000, '.3f'))
        encoder_resolution = self._master.mf.trigger_scan_p.get_encoder_resolution()
        if (dx is not None) and (encoder_resolution is not None):
            interval = int(dx / encoder_resolution)
            self._master.mf.trigger_scan_p.set_tc_en_interval(interval)
            self._master.mf.trigger_test_p.right_f.set_interval(str(interval))
        self.tc_cal_sample_count()
        self.tc_max_speed_cmd()

    def tc_max_speed_cmd(self) -> None:
        shz = self._master.tf.sample_rate_led_f.get_tf_sample_rate()
        dx = self._master.mf.trigger_scan_p.get_dx_value()
        if len(shz) > 0 and (dx is not None):
            max_speed = "{:.2f}".format(int(shz) * dx * 0.9 / 1000).rstrip('0').rstrip('.')
            self._master.mf.trigger_scan_p.set_max_speed(max_speed)

    def tc_trig_on_return_cmd(self) -> None:
        sel = self._master.mf.trigger_scan_p.get_tc_trig_on_return()
        self._master.mf.trigger_test_p.right_f.set_tt_trig_on_return(sel)

    def tc_reset_ctn_cmd(self) -> None:
        selected_mode = self._master.mf.trigger_scan_p.get_tc_trig_mode_value()
        if selected_mode != self.mf_tt_ctn:
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_ctn)
            self.tc_mode_select_cmd()

    # endregion

    def on_close_cmd(self):
        self._master.mf.trigger_scan_p.stop_auto_update_sample_counter()
        ip = self._master.lf.conn_f.get_ip()
        if ip:
            self.app_prc.set_filter_ip(ip)
            self.app_prc.save_data_filter()


class ConnCallback(object):
    def __init__(self, master: App, conn_prc: ConnProcess, app_callback: AppCallback) -> None:
        self._master = master
        self._conn_prc = conn_prc
        self._app_cb = app_callback
        self.tf_sta = self._master.tf.device_data_flow_switch_f.STA
        self.tf_sto = self._master.tf.device_data_flow_switch_f.STO
        self.tf_ctn = self._master.tf.device_measurement_mode_f.CTN
        self.tf_trg = self._master.tf.device_measurement_mode_f.TRG
        self.tf_tre = self._master.tf.device_measurement_mode_f.TRE
        self.mf_tt_ctn = self._master.mf.trigger_test_p.right_f.CTN
        self.mf_tt_trg = self._master.mf.trigger_test_p.right_f.TRG
        self.mf_tt_tre = self._master.mf.trigger_test_p.right_f.TRE
        self.mf_tc_ctn = self._master.mf.trigger_scan_p.top_left_f.second_r_f.CTN
        self.mf_tc_sync = self._master.mf.trigger_scan_p.top_left_f.second_r_f.SYNC
        self.mf_tc_tre = self._master.mf.trigger_scan_p.top_left_f.second_r_f.TRE
        self.axis_map = {'x': '0', 'y': '1', 'z': '2', 'u': '3', 'v': '4'}

    # region Top frame callback

    def output_signal_cmd(self) -> None:
        signal_list = self._master.tf.output_signal_f.get_output_signal()
        if signal_list:
            args = signal_list.replace(',', ' ').replace(';', ' ')
            self._conn_prc.sync_exec('SODX ' + args)

    def sample_rate_cmd(self) -> None:
        shz = self._master.tf.sample_rate_led_f.get_tf_sample_rate()
        self._conn_prc.async_exec(cmd_str='SHZ {}'.format(shz))

    def led_cmd(self) -> None:
        lai = self._master.tf.sample_rate_led_f.get_tf_led()
        self._conn_prc.async_exec('LAI {}'.format(lai))

    def threshold_cmd(self) -> None:
        thr = self._master.tf.threshold_f.get_threshold()
        self._conn_prc.async_exec('THR {}'.format(thr))

    def tf_trig_mode_select_cmd(self) -> None:
        self._app_cb.tf_trig_mode_select_cmd()
        selected_mode = self._master.tf.device_measurement_mode_f.get_tf_trig_mode_value()
        if selected_mode == self.tf_ctn:
            self._conn_prc.async_exec('CTN')
        elif selected_mode == self.tf_trg:
            self._conn_prc.async_exec('TRG')
        elif selected_mode == self.tf_tre:
            self._conn_prc.async_exec('TRE')
            self.use_encoder_trig_cmd()

    def tf_flow_switch_select_cmd(self) -> None:
        selected_option = self._master.tf.device_data_flow_switch_f.get_data_flow_option_value()
        if selected_option == self.tf_sta:
            self._conn_prc.sync_exec('STA')
        elif selected_option == self.tf_sto:
            self._conn_prc.sync_exec('STO')

    # endregion

    # region Top frame -  Samples update callback(focus)

    def update_focus_distance(self) -> None:
        if self._conn_prc.samples_ready.is_set():
            if self._conn_prc.last_distance_1_int16_ch1 is not None:
                self._master.tf.focus_f.set_distance_prog_bar_value(str(self._conn_prc.last_distance_1_int16_ch1))
            if self._conn_prc.last_distance_1_ch1 is not None:
                self._master.tf.focus_f.set_distance_value("{:10.2f}".format(self._conn_prc.last_distance_1_ch1))

    # endregion

    # region Left frame callback
    def dark_cmd(self) -> None:
        self._master.lf.dark_ref_f.disable_dark_button()
        self._conn_prc.async_exec(cmd_str='DRK')

    def fast_dark_cmd(self) -> None:
        self._master.lf.dark_ref_f.disable_fast_dark_button()
        self._conn_prc.async_exec(cmd_str='FDK')

    def probe_select_cmd(self) -> None:
        selected_probe = self._master.lf.probe_sel_f.get_selected_probe()
        probe_index = selected_probe[:int(selected_probe.find(':'))]
        self._master.lf.probe_sel_f.set_probe(int(probe_index))
        self._conn_prc.async_exec(cmd_str='SEN {}'.format(probe_index))
        self._conn_prc.async_exec(cmd_str='SCA ?', gui_update=True)
        full_scale = int(self._conn_prc.probe_list[int(probe_index)]['Full Scale'].replace('um', '').strip())
        self._conn_prc.data_acq.set_full_scale(full_scale)
        if self._conn_prc.probe_list[int(probe_index)]['Pitch']:
            pitch = self._conn_prc.probe_list[int(probe_index)]['Pitch'].replace('um', '').strip()
            self._master.mf.trigger_scan_p.set_dy_value(pitch)

    def number_of_peak_cmd(self) -> None:
        nop = self._master.lf.multilayer_stn_f.get_lf_number_of_peak()
        if nop.isdigit():
            self._conn_prc.async_exec(cmd_str='NOP ' + nop)
        else:
            self._master.lf.multilayer_stn_f.set_lf_number_of_peak('')

    def data_sample_cmd(self) -> None:
        avd = self._master.lf.average_f.get_data_sample()
        if avd.isdigit():
            self._conn_prc.async_exec(cmd_str='AVD ' + avd)
        else:
            self._master.lf.average_f.set_data_sample('')

    def spectrum_average_cmd(self) -> None:
        avs = self._master.lf.average_f.get_spectrum_average()
        if avs.isdigit():
            self._conn_prc.async_exec(cmd_str='AVS ' + avs)
        else:
            self._master.lf.average_f.set_spectrum_average('')

    # endregion

    # region Main frame callback

    """ Connection frame callback """

    # region
    def conn_test_cmd(self) -> None:
        btn_state = self._master.mf.connection_p.top_left_f.get_btn_color()
        if btn_state == 'n':
            """ Start connection test """
            self._conn_prc.flush_connection_buffer()
            self._master.mf.connection_p.top_left_f.set_samples_y_limit(0, 10)
            self._conn_prc.start_conn_samples_thread()
            self._master.mf.connection_p.bottom_left_f.set_samples_y_limit(0, 10)
            self._conn_prc.start_conn_distance_1_thread()
            self._master.mf.connection_p.top_left_f.set_btn_greed()
        elif btn_state == 'g':
            """ Pause connection test """
            self._conn_prc.pause_conn_samples()
            self._conn_prc.pause_conn_distance_1()
            self._master.mf.connection_p.top_left_f.set_btn_red()
        else:
            """ Resume connection test """
            self._conn_prc.resume_conn_samples()
            self._conn_prc.resume_conn_distance_1()
            self._master.mf.connection_p.top_left_f.set_btn_greed()

    def conn_modify_ip_cmd(self) -> None:
        ip = self._master.mf.connection_p.get_conn_page_ip()
        current_ip = self._master.lf.conn_f.get_ip()
        if ip != current_ip:
            ip_str = ' '.join(ip.split('.'))
            self._conn_prc.async_exec('IPCN ' + ip_str)
            self._conn_prc.samples_ready.clear()
            self._conn_prc.set_connection_off_flags()
            self._conn_prc.conn_callback(-1)

    # endregion

    """ Initial frame callback """

    # region
    def get_all_probes_info_cmd(self) -> None:
        self._conn_prc.async_exec('SENX enum ?')

    # endregion

    """ Focus frame callback """

    # region
    def focus_set_button_cmd(self) -> None:
        freq = self._master.mf.focus_p.get_focus_freq()
        lai = self._master.mf.focus_p.get_focus_led()
        self._conn_prc.async_exec('SHZ {}'.format(freq))
        self._conn_prc.async_exec('LAI {}'.format(lai))

    def focus_spectrum_button_cmd(self, sync=True) -> None:
        btn_color = self._master.mf.focus_p.get_focus_spectrum_btn_color()
        if btn_color == 'n':
            self._master.mf.focus_p.set_focus_spectrum_btn_green()
            self._conn_prc.spectrum_is_on = True
            self._master.mf.focus_p.focus_spectrum_f.update_focus_p_spectrum()
        else:
            self._master.mf.focus_p.set_focus_spectrum_btn_normal()
            self._conn_prc.spectrum_is_on = False
            self._master.mf.focus_p.focus_spectrum_f.stop_focus_p_spectrum()
        if sync:
            self.multilayer_spectrum_button_cmd(sync=False)

    def focus_spectrum_channel_entry_cmd(self) -> None:
        channel_str = self._master.mf.focus_p.get_focus_spectrum_channel()
        set_channel_int = 0
        set_channel_str = '0'
        if channel_str.isdigit():
            channel_int = int(channel_str)
            if 0 < channel_int < self._conn_prc.conf['NCH']:
                set_channel_int = channel_int
                set_channel_str = str(channel_int)
            elif channel_int >= self._conn_prc.conf['NCH']:
                set_channel_int = self._conn_prc.conf['NCH'] - 1
                set_channel_str = str(set_channel_int)
        self._conn_prc.spectrum_channel = set_channel_int
        self._master.mf.focus_p.set_focus_spectrum_channel(set_channel_str)

    def update_focus_p_spectrum_cmd(self) -> None:
        current_tab_index = self._master.mf.notebook.index(self._master.mf.notebook.select())
        if self._conn_prc.spectrum_is_on:
            if current_tab_index == 3 and self._conn_prc.spectrum_data is not None:
                self._master.mf.focus_p.update_focus_spectrum(self._conn_prc.spectrum_data)

    def multichannel_profile_view_button_cmd(self) -> None:
        btn_color = self._master.mf.focus_p.get_multichannel_profile_view_btn_color()
        if btn_color == 'n':
            if len(self._master.mf.focus_p.get_multichannel_profile_view_id()) == 0:
                id_list = self._master.mf.focus_p.get_multichannel_profile_view_id_list()
                if len(id_list) > 0:
                    self._master.mf.focus_p.set_multichannel_profile_view_id(id_list[0])
            self._master.mf.focus_p.set_multichannel_profile_view_btn_green()
            self._conn_prc.multichannel_view_is_on = True
            self._master.mf.focus_p.multi_prof_view_f.update_y_lim_to_chart()
            self._master.mf.focus_p.multi_prof_view_f.update_prof_view()

        else:
            self._master.mf.focus_p.set_multichannel_profile_view_btn_normal()
            self._conn_prc.multichannel_view_is_on = False
            self._master.mf.focus_p.multi_prof_view_f.stop_prof_view()

    def update_multichannel_prof_view(self) -> None:
        current_tab_index = self._master.mf.notebook.index(self._master.mf.notebook.select())
        if self._conn_prc.multichannel_view_is_on:
            if current_tab_index == 3:
                selected_id_str = self._master.mf.focus_p.get_multichannel_profile_view_id()
                if selected_id_str == 'Distance 1':
                    self._master.mf.focus_p.update_multichannel_profile_view(self._conn_prc.last_distance_1)
                elif selected_id_str == 'Intensity 1':
                    self._master.mf.focus_p.update_multichannel_profile_view(self._conn_prc.last_intensity_1, True)
    # endregion

    """ Trigger Test callback """

    # region
    def trig_test_mode_select_cmd(self) -> None:
        self._app_cb.trig_test_mode_select_cmd()
        selected_mode = self._master.mf.trigger_test_p.right_f.get_tt_trig_mode_value()
        if selected_mode == self.mf_tt_ctn:
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_ctn)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_ctn)
            self._conn_prc.async_exec('CTN')
        elif selected_mode == self.mf_tt_trg:
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_trg)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(None)
            self._conn_prc.async_exec('TRG')
        elif selected_mode == self.mf_tt_tre:
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_tre)
            self._master.mf.trigger_scan_p.set_tc_trig_mode_value(self.mf_tc_tre)
            self.use_encoder_trig_cmd()
            self._conn_prc.async_exec('TRE')

    def software_trig_cmd(self) -> None:
        if self._master.mf.trigger_test_p.right_f.get_tt_trig_mode_value() == self.mf_tt_trg:
            self._master.mf.trigger_test_p.right_f.set_tt_trig_mode_value(self.mf_tt_ctn)
            self._master.tf.device_measurement_mode_f.set_tf_trig_mode_value(self.tf_ctn)
            self._master.mf.trigger_scan_p.top_left_f.second_r_f.set_tc_trig_mode_value(self.mf_tc_ctn)
        self._conn_prc.async_exec('STR')
        if self._master.mf.trigger_test_p.right_f.get_tt_trig_mode_value() == self.mf_tt_tre:
            self._conn_prc.data_acq.get_last_sample()

    def use_encoder_trig_cmd(self) -> None:
        self._app_cb.tt_use_encoder_trig_cmd()
        if self._master.mf.trigger_test_p.right_f.get_use_encoder_trig() == 1:
            self._conn_prc.async_exec('ETR 3 1')
            self.endless_trig_cmd()
            self.stop_pos_cmd()
            self.interval_cmd()
            self.tt_trig_on_return_cmd()
            self.tt_axis_sel_cmd()
            self.start_pos_cmd()
        else:
            self._conn_prc.async_exec('ETR 3 0')

    def endless_trig_cmd(self) -> None:
        self._conn_prc.async_cmd.etr_cmds_index.append(7)
        self._conn_prc.sync_exec('ETR 7 ' + str(self._master.mf.trigger_test_p.right_f.get_endless_trig()))

    def tt_trig_on_return_cmd(self) -> None:
        self._app_cb.tt_trig_on_return_cmd()
        self._conn_prc.async_exec('ETR 4 ' + str(self._master.mf.trigger_test_p.right_f.get_tt_trig_on_return()))

    def tt_axis_sel_cmd(self) -> None:
        self._app_cb.tt_axis_sel_cmd()
        self._conn_prc.async_exec('ETR 5 ' + self.axis_map[self._master.mf.trigger_test_p.right_f.get_tt_axis()])

    def start_pos_cmd(self) -> None:
        self._conn_prc.async_exec('ETR 0 ' + self._master.mf.trigger_test_p.right_f.get_start_pos())

    def interval_cmd(self) -> None:
        self._conn_prc.async_exec('ETR 2 ' + self._master.mf.trigger_test_p.right_f.get_interval())

    def stop_pos_cmd(self) -> None:
        self._conn_prc.async_exec('ETR 1 ' + self._master.mf.trigger_test_p.right_f.get_stop_pos())

    def tt_set_trig_pos_cmd(self) -> None:
        axis = self.axis_map[self._master.mf.trigger_test_p.right_f.get_tt_axis()]
        trig_pos = self._master.mf.trigger_test_p.right_f.get_trig_axis_encoder_pos()
        self._conn_prc.async_exec('ENC {} {}'.format(axis, trig_pos))
        if axis == '0':
            self._master.mf.trigger_test_p.set_encoder_x_value(trig_pos)
        elif axis == '1':
            self._master.mf.trigger_test_p.set_encoder_y_value(trig_pos)
        elif axis == '2':
            self._master.mf.trigger_test_p.set_encoder_z_value(trig_pos)

    def order_encoder_cmd(self) -> None:
        rsp = self._conn_prc.sync_exec('ENC 0 ?')
        if rsp and rsp.error_code == 0:
            self._master.mf.trigger_test_p.set_encoder_x_value(rsp.args[1])
        rsp = self._conn_prc.sync_exec('ENC 1 ?')
        if rsp and rsp.error_code == 0:
            self._master.mf.trigger_test_p.set_encoder_y_value(rsp.args[1])
        rsp = self._conn_prc.sync_exec('ENC 2 ?')
        if rsp and rsp.error_code == 0:
            self._master.mf.trigger_test_p.set_encoder_z_value(rsp.args[1])

    def check_trigger_lost_cmd(self) -> None:
        btn_state = self._master.mf.trigger_test_p.get_check_check_trigger_btn_color()
        if btn_state == 'n':
            self._conn_prc.start_trigger_lost_verify_thread()
        elif btn_state == 'g':
            self._conn_prc.stop_trigger_lost_verify_thread()

    # endregion

    """ Trigger Scan callback """

    # region
    def trig_scan_mode_select_cmd(self) -> None:
        self._app_cb.tc_mode_select_cmd()
        selected_mode = self._master.mf.trigger_scan_p.get_tc_trig_mode_value()
        if selected_mode == self.mf_tc_ctn:
            self._conn_prc.sync_exec('CTN')
        elif selected_mode == self.mf_tc_sync:
            self._conn_prc.sync_exec('TRE')
            self.use_encoder_trig_cmd()
        elif selected_mode == self.mf_tc_tre:
            self.use_encoder_trig_cmd()
            self._conn_prc.sync_exec('TRE')

    def trig_scan_axis_sel_cmd(self) -> None:
        self._app_cb.tc_axis_sel_cmd()
        self._conn_prc.sync_exec('ETR 5 ' + self.axis_map[self._master.mf.trigger_scan_p.get_tc_axis()])

    def trig_scan_en_start_pos_cmd(self) -> None:
        en_start_pos = self._master.mf.trigger_scan_p.get_tc_en_start_pos()
        if en_start_pos is not None:
            self._app_cb.tc_en_start_pos_cmd()
            self._conn_prc.sync_exec('ETR 0 ' + str(en_start_pos))

    def trig_scan_en_stop_pos_cmd(self) -> None:
        en_stop_pos = self._master.mf.trigger_scan_p.get_tc_en_stop_pos()
        if en_stop_pos is not None:
            self._app_cb.tc_en_stop_pos_cmd()
            self._conn_prc.sync_exec('ETR 1 ' + str(en_stop_pos))

    def trig_scan_en_interval_cmd(self) -> None:
        en_interval = self._master.mf.trigger_scan_p.get_tc_en_interval()
        if en_interval is not None:
            self._app_cb.tc_en_interval_cmd()
            self._conn_prc.sync_exec('ETR 2 ' + str(en_interval))

    def trig_scan_pos_start_pos_cmd(self) -> None:
        pass

    def trig_scan_pos_stop_pos_cmd(self) -> None:
        pass

    def trig_scan_pos_interval_cmd(self) -> None:
        pass

    def trig_scan_trig_on_return_cmd(self) -> None:
        self._app_cb.tc_trig_on_return_cmd()
        self._conn_prc.sync_exec('ETR 4 ' + str(self._master.mf.trigger_scan_p.get_tc_trig_on_return()))

    def trig_scan_set_trig_pos_cmd(self) -> None:
        axis = self.axis_map[self._master.mf.trigger_scan_p.get_tc_axis()]
        trig_pos = self._master.mf.trigger_scan_p.get_tc_trig_axis_encoder_pos()
        self._conn_prc.async_exec('ENC {} {}'.format(axis, trig_pos))
        self._master.mf.trigger_scan_p.set_tc_encoder_bar(trig_pos)
        if axis == '0':
            self._master.mf.trigger_test_p.set_encoder_x_value(trig_pos)
        elif axis == '1':
            self._master.mf.trigger_test_p.set_encoder_y_value(trig_pos)
        elif axis == '2':
            self._master.mf.trigger_test_p.set_encoder_z_value(trig_pos)

    def trig_scan_reset_ctn_cmd(self) -> None:
        selected_mode = self._master.mf.trigger_scan_p.get_tc_trig_mode_value()
        if selected_mode != self.mf_tc_ctn:
            self._app_cb.tc_reset_ctn_cmd()
            self.trig_test_mode_select_cmd()

    def trig_scan_start_scan_cmd(self) -> None:
        self._conn_prc.start_scan_thread()

    def trig_scan_stop_scan_cmd(self) -> None:
        self._conn_prc.stop_scan_thread()

    def trig_scan_save_data_cmd(self) -> None:
        if self._conn_prc.scan_data_is_ready():
            data_format = self._master.mf.trigger_scan_p.get_tc_data_format()
            filepath = asksaveasfilename(defaultextension=data_format[1:], filetypes=[("Text Files", data_format)])
            if filepath:
                _peak_ids = self._conn_prc.get_scan_peak_ids()
                distance_ids = [num for num in _peak_ids if int(num) % 2 == 0]
                intensity_ids = [num for num in _peak_ids if int(num) % 2 != 0]
                for i in range(len(distance_ids)):
                    distance_data = self._conn_prc.get_scan_data(id_str=distance_ids[i])
                    distance_header = self._conn_prc.default_header.copy()
                    ln_sample_cnt = self._conn_prc.get_scan_data_line_sample_cnt()
                    ln_cnt = self._conn_prc.get_scan_data_ln_cnt()
                    ch_cnt = self._conn_prc.get_scan_data_ch_cnt()
                    dx = self._conn_prc.get_scan_data_dx()
                    dy = self._conn_prc.get_scan_data_dy()
                    distance_header['x-pixels'] = ln_sample_cnt
                    distance_header['y-pixels'] = ln_cnt * ch_cnt
                    distance_header['x-length'] = ln_sample_cnt * dx * 1000 if ln_sample_cnt * dx * 1000 > 0 else 0
                    distance_header['y-length'] = ln_cnt * ch_cnt * dy * 1000 if ln_cnt * ch_cnt * dy * 1000 > 0 else 0
                    distance_header['z-unit'] = 'um'
                    distance_filepath = os.path.splitext(filepath)[0] + '_distance_' + str(i+1) + data_format[1:]
                    intensity_data = self._conn_prc.get_scan_data(id_str=intensity_ids[i])
                    intensity_header = distance_header.copy()
                    intensity_header['z-unit'] = '%'
                    intensity_filepath = os.path.splitext(filepath)[0] + '_intensity_' + str(i+1) + data_format[1:]
                    if data_format == '*.asc':
                        distance_header['File Format'] = 'ASCII'
                        intensity_header['File Format'] = 'ASCII'
                        write_file.write_asc_file(filename=distance_filepath, header_dict=distance_header,
                                                  data=distance_data)
                        write_file.write_asc_file(header_dict=intensity_header, filename=intensity_filepath,
                                                  data=intensity_data)
                    else:
                        distance_header['File Format'] = 'bcrf_unicode'
                        distance_data = distance_data.flatten('F')
                        write_file.write_bcrf_file(filename=distance_filepath, data=distance_data,
                                                   x_pixels=distance_header['x-pixels'],
                                                   y_pixels=distance_header['y-pixels'],
                                                   x_length=distance_header['x-length'],
                                                   y_length=distance_header['y-length'],
                                                   z_unit=distance_header['z-unit'])
                        intensity_data = intensity_data.flatten('F')
                        write_file.write_bcrf_file(filename=intensity_filepath, data=intensity_data,
                                                   x_pixels=intensity_header['x-pixels'],
                                                   y_pixels=intensity_header['y-pixels'],
                                                   x_length=intensity_header['x-length'],
                                                   y_length=intensity_header['y-length'],
                                                   z_unit=intensity_header['z-unit'])
                    log.info('Distance File Saved to: {}'.format(distance_filepath))
                    log.info('Intensity File Saved to: {}'.format(intensity_filepath))

    def trig_scan_select_signal_cmd(self) -> None:
        self._conn_prc.plot_selected_id()

    # endregion

    """ Multi-Layer Frame callback """

    # region
    def multilayer_spectrum_button_cmd(self, sync=True) -> None:
        btn_color = self._master.mf.multi_layer_setting_p.get_multilayer_spectrum_btn_color()
        if btn_color == 'n':
            self._master.mf.multi_layer_setting_p.set_multilayer_spectrum_btn_green()
            self._conn_prc.spectrum_is_on = True
            self._master.mf.multi_layer_setting_p.multi_layer_spectrum_f.update_multilayer_p_spectrum()
        else:
            self._master.mf.multi_layer_setting_p.set_multilayer_spectrum_btn_normal()
            self._conn_prc.spectrum_is_on = False
            self._master.mf.multi_layer_setting_p.multi_layer_spectrum_f.stop_multilayer_p_spectrum()
        if sync:
            self.focus_spectrum_button_cmd(sync=False)

    def multilayer_spectrum_channel_entry_cmd(self) -> None:
        channel_str = self._master.mf.multi_layer_setting_p.get_multilayer_spectrum_channel()
        set_channel_int = 0
        set_channel_str = '0'
        if channel_str.isdigit():
            channel_int = int(channel_str)
            if 0 < channel_int < self._conn_prc.conf['NCH']:
                set_channel_int = channel_int
                set_channel_str = str(channel_int)
            elif channel_int >= self._conn_prc.conf['NCH']:
                set_channel_int = self._conn_prc.conf['NCH'] - 1
                set_channel_str = str(set_channel_int)
        self._conn_prc.spectrum_channel = set_channel_int
        self._master.mf.multi_layer_setting_p.set_multilayer_spectrum_channel(set_channel_str)

    def update_multilayer_p_spectrum_cmd(self) -> None:
        current_tab_index = self._master.mf.notebook.index(self._master.mf.notebook.select())
        if self._conn_prc.spectrum_is_on:
            if current_tab_index == 6 and self._conn_prc.spectrum_data:
                self._master.mf.multi_layer_setting_p.update_multilayer_spectrum(self._conn_prc.spectrum_data)
    # endregion

    # endregion

    # region Main frame - Samples update callback(trigger test)

    def update_trigger_test(self):
        if self._conn_prc.samples_ready.is_set():
            if self._conn_prc.last_sample_cnt is not None:
                sample_cnt = str(self._conn_prc.last_sample_cnt)
                self._master.mf.trigger_test_p.set_sample_counter_value(sample_cnt)

    # endregion

    # region Main frame - Samples update callback(trigger scan)

    def update_trigger_scan(self) -> None:
        if self._conn_prc.samples_ready.is_set():
            if self._conn_prc.last_sample_cnt is not None:
                sample_cnt = str(self._conn_prc.last_sample_cnt)
                self._master.mf.trigger_scan_p.set_tc_sample_counter_bar(sample_cnt)
            if self._conn_prc.last_distance_1_ch1 is not None:
                distance = str(self._conn_prc.last_distance_1_int16_ch1)
                self._master.mf.trigger_scan_p.set_tc_distance_bar(distance)

    # endregion

    # region Command frame callback

    def command_box_cmd(self) -> None:
        cmd_str = self._master.cmd_f.get_entry()
        if 'SODX' in cmd_str:
            self._conn_prc.sync_exec(cmd_str)
        elif 'ETR 7' in cmd_str:
            self._conn_prc.sync_exec(cmd_str)
        elif 'STA' in cmd_str:
            rsp = self._conn_prc.sync_exec(cmd_str)
            if rsp:
                self._master.tf.device_data_flow_switch_f.set_data_flow_option_value(self.tf_sta)
                self.tf_flow_switch_select_cmd()
        elif 'STO' in cmd_str:
            rsp = self._conn_prc.sync_exec(cmd_str)
            if rsp:
                self._master.tf.device_data_flow_switch_f.set_data_flow_option_value(self.tf_sto)
                self.tf_flow_switch_select_cmd()
        elif 'MED' in cmd_str:
            self._conn_prc.sync_exec(cmd_str)
        # Manually unlock the scan button status, in case of the CLS2 name string cannot be identified.
        elif cmd_str == 'unlock scan':
            self._master.mf.trigger_scan_p.tc_start_scan_btn_stat('True')
        else:
            self._conn_prc.async_exec(cmd_str)

    # endregion


""" Scan Thread Classes """


class ScanThread(Thread):
    def __init__(self, master: App, conn, close_cmd=None, sync_exec: Callable = None):
        super().__init__()
        self.master = master
        self._thread_on = Event()
        self._thread_on.clear()
        self.conn = conn
        self._forced_stop = None
        self.data_buffer = {}
        self._data_ready = False
        self._is_sat_int = False
        self.close_cmd = close_cmd
        self.last_sample_cnt = 0
        self._line_sample_cnt = None
        self._line_cnt = None
        self._ch_cnt = None
        self._dx = None
        self._dy = None
        self.samples = None
        self.gen_sig_info, self.sig_ids = None, None
        self.global_sig_ids, self.peak_sig_ids = None, None
        self._mea_range = 0
        self._intensity_saturation_level = 0
        self.encoder_id = None
        self.sync_exe_function = sync_exec
        self.id_to_units = {
            '16640': 'um',
            '16641': '%',
            '16648': 'um',
            '16649': '%',
            '16656': 'um',
            '16657': '%',
            '16664': 'um',
            '16665': '%',
            'sat': '%'
        }
        self._id_to_name = {
            '16640': 'Distance 1',
            '16641': 'Intensity 1',
            '16648': 'Distance 2',
            '16649': 'Intensity 2',
            '16656': 'Distance 3',
            '16657': 'Intensity 3',
            '16664': 'Distance 4',
            '16665': 'Intensity 4'
        }

    def run(self):
        self.master.mf.trigger_scan_p.set_tc_start_scan_btn(True)  # Set the start button to green
        self._thread_on.set()
        self.init()
        self.conn.send_command_string('STA')
        self._mea_range = self.conn.send_query('SCA').args[0]
        self._intensity_saturation_level = int(self.master.mf.trigger_scan_p.get_tc_saturation_level())
        self.master.tf.device_data_flow_switch_f.set_data_flow_option_value(0)  # set data flow switch to STA
        is_plot = self.master.mf.trigger_scan_p.right_f.first_row_f.display_switch_status.get() == 'on'
        selected_id = None
        if is_plot:
            peak_ids_name = [f"{_id} ({self._id_to_name[_id]})" for _id in self.peak_sig_ids]
            if self._is_sat_int:
                peak_ids_name.append('16641 (highlight saturation)')
            self.master.mf.trigger_scan_p.tc_set_peak_id_options(peak_ids_name)
            selected_id = self.master.mf.trigger_scan_p.tc_get_peak_id()
            if len(selected_id) == 0:
                selected_id = self.peak_sig_ids[0]
            else:
                # Get only the first part of the peak signal string
                selected_id = selected_id.split()[0]
        for id_str in self.peak_sig_ids + self.global_sig_ids:
            self.data_buffer[id_str] = None
        start_time = time.time()
        while self._thread_on.is_set():
            self.master.mf.trigger_scan_p.tc_reset_plot_scale()
            for line in range(self._line_cnt):
                log.info('Start scanning line {}..'.format(line + 1))
                _ = self.conn.activate_auto_buffer_mode(sample_cnt=self._line_sample_cnt, flush_buffer=True)
                self.samples = self.conn.get_auto_buffer_samples(self._line_sample_cnt,
                                                                 self.conn.get_single_output_sample_size())
                self.last_sample_cnt = 0
                while self.last_sample_cnt < self._line_sample_cnt and self._thread_on.is_set():
                    sleep(0.25)
                    ret = self.get_sliced_auto_buffer_data(line)
                    if ret and is_plot:
                        self.plot_data_to_gui(selected_id)
                self.conn.deactivate_auto_buffer_mode()
                log.info('Line {} scan finished'.format(line + 1))
            self._thread_on.clear()
            if is_plot:
                self.master.mf.trigger_scan_p.tc_set_peak_id(f"{selected_id} ({self._id_to_name[selected_id]})")
                self.master.mf.trigger_scan_p.tc_set_plot_unit(self.id_to_units[selected_id])
        end_time = time.time()
        elapsed_time = end_time - start_time
        plotting_log = '含繪圖' if is_plot else '不含繪圖'
        total_sample_cnt = self._line_cnt * self._line_sample_cnt
        log.info(f"共 {total_sample_cnt} 筆 sample, 資料收集時間: {elapsed_time:.3f} 秒, ({plotting_log})")
        log.info('Trigger Scan Finished')
        self.master.cmd_f.insert_textbox(f"[App Info] Collected {total_sample_cnt} samples. Took {elapsed_time:.3f} seconds.")
        sleep(0.3)  # To prevent user to click too fast before the data_acq thread has not been started
        if self.close_cmd is not None:
            self.close_cmd()
        self.master.mf.trigger_scan_p.set_tc_start_scan_btn(False)  # Set the start button to normal
        self.master.mf.trigger_scan_p.start_auto_update_sample_counter()
        if self._forced_stop:
            sleep(0.5)
            log.info('Trigger Scan Aborted')
            self.master.mf.trigger_scan_p.set_tc_start_scan_btn(False)  # Set the start button to normal
            self._data_ready = False
        else:
            self._data_ready = True
        self.sync_exe_function('SODX 83 16640 16641')

    def init(self):
        self.last_sample_cnt = 0
        self.data_buffer = {}
        self.master.mf.trigger_scan_p.tc_clear_plot()
        self.master.mf.trigger_scan_p.tc_set_peak_id('')
        self.master.mf.trigger_scan_p.tc_set_peak_id_options([])
        self._dx = self.master.mf.trigger_scan_p.get_dx_value()
        if self._dx is None:
            self.master.mf.trigger_scan_p.set_dx_value('2')
            self._dx = 2.0
        self._dy = self.master.mf.trigger_scan_p.get_dy_value()
        self._line_cnt = self.master.mf.trigger_scan_p.get_tc_y_line_count()
        self._line_sample_cnt = int(self.master.mf.trigger_scan_p.get_tc_sample_count())
        self.gen_sig_info, self.sig_ids = self.conn.get_output_signal_infos()
        ids = np.array(self.sig_ids)[:, 1]
        self.global_sig_ids = list(map(str, ids[:self.gen_sig_info.global_sig_cnt]))
        self.peak_sig_ids = list(map(str, ids[self.gen_sig_info.global_sig_cnt:]))
        self._is_sat_int = self.master.mf.trigger_scan_p.right_f.first_row_f.sat_int_switch_status.get() == 'on'

    def get_sliced_auto_buffer_data(self, line):
        cnt = self.conn.get_auto_buffer_saved_sample_count()
        if cnt == 0 or cnt <= self.last_sample_cnt:
            return False
        sliced_data = Data(samples=self.samples[self.last_sample_cnt: cnt, :], sample_cnt=cnt - self.last_sample_cnt,
                           gen_signal_info=self.gen_sig_info, signal_info=self.sig_ids, err_code=0,
                           dll_h=self.conn.dll_handle())
        self._ch_cnt = self.gen_sig_info.channel_cnt
        for id_str in self.peak_sig_ids:
            if self.data_buffer[id_str] is None:
                self.data_buffer[id_str] = np.empty((self._line_sample_cnt,
                                                     self._line_cnt * self._ch_cnt))
            sliced_peak_data = sliced_data.get_signal_values_all(int(id_str))
            if id_str == '16640' or id_str == '16648' or id_str == '16656' or id_str == '16664':
                sliced_peak_data = self.unit_to_um(sliced_peak_data)
            if id_str == '16641' or id_str == '16649' or id_str == '16657' or id_str == '16665':
                sliced_peak_data = self.intensity_data_handle(sliced_peak_data, cnt, line)
            self.data_buffer[id_str][self.last_sample_cnt:cnt,
            line * self._ch_cnt:(line + 1) * self._ch_cnt] = sliced_peak_data
        for id_str in self.global_sig_ids:
            glob_signals = sliced_data.get_signal_values_all(int(id_str))
            if self.data_buffer[id_str] is None:
                self.data_buffer[id_str] = glob_signals
            else:
                self.data_buffer[id_str] = np.concatenate((self.data_buffer[id_str], glob_signals))
        self.last_sample_cnt = cnt

        return True

    def unit_to_um(self, raw_data):
        return raw_data * self._mea_range / 32768

    def intensity_data_handle(self, raw_data, cnt, line):
        if self._is_sat_int:
            if 'sat' not in self.data_buffer.keys():
                self.data_buffer['sat'] = np.empty((self._line_sample_cnt,
                                                    self._line_cnt * self._ch_cnt)).astype(np.int16)
            percentage_data = numpy.around((raw_data / self._intensity_saturation_level) * 100, 3)
            percentage_data[percentage_data < 0] = 999
            self._ch_cnt = self.gen_sig_info.channel_cnt

            self.data_buffer['sat'][self.last_sample_cnt:cnt,
            line * self._ch_cnt:(line + 1) * self._ch_cnt] = percentage_data.astype(np.int16)
        raw_data = raw_data.astype(np.int16) & 0x7FFF  # remove the sign data in the intensity data
        return numpy.around((raw_data / self._intensity_saturation_level) * 100, 3)

    def plot_data_to_gui(self, id_str):
        self.master.mf.trigger_scan_p.tc_set_scan_plot(self.data_buffer[id_str].T)
        if '83' in self.global_sig_ids:
            self.master.mf.trigger_scan_p.set_tc_sample_counter_bar(str(int(self.data_buffer['83'][-1])))
        if self.encoder_id in self.global_sig_ids:
            self.master.mf.trigger_scan_p.set_tc_encoder_bar(str(int(self.data_buffer[self.encoder_id][-1])))

    def stop_scan(self):
        self._thread_on.clear()
        self._forced_stop = True

    def scan_thread_on(self):
        return self._thread_on.is_set()

    def get_data(self, id_str: str) -> numpy.array:
        if self.data_buffer:
            return self.data_buffer[id_str]
        else:
            return None

    def get_peak_ids(self) -> list:
        return self.peak_sig_ids

    def get_ch_cnt(self) -> int:
        return self._ch_cnt

    def get_ln_cnt(self) -> int:
        return self._line_cnt

    def get_dx(self) -> float:
        return self._dx

    def get_dy(self) -> float:
        return self._dy

    def get_line_sample_cnt(self) -> int:
        return self._line_sample_cnt

    def data_is_ready(self) -> bool:
        return self._data_ready


class ConnSamplesThread(Thread):
    def __init__(self, master: App, queue: Queue = None, update_freq: int = 1):
        super().__init__()
        self.daemon = True
        self._master = master
        self._queue = queue
        self._update_freq = update_freq
        self._update_period = 1 / self._update_freq
        self._time_interval = 10
        self._time_index = 0
        self._samples_buffer = None
        self._thread_on = Event()
        self._thread_on.clear()
        """ 
        self._thread_resume event shows the thread is paused or not.
        If the self._thread_resume is set, the thread is not pausing.
        If the self._thread_resume is not set, the thread is paused.
        """
        self._thread_resume = Event()

    def run(self):
        self._samples_buffer = None
        data_processing_time = 0
        self.resume_thread()
        while self._thread_on.is_set():
            self._thread_resume.wait()
            data_list = []
            start_time_1 = timeit.default_timer()
            sleep_time = self._update_period - data_processing_time
            """ Remove sleep time if data processing time is longer than update_period """
            sleep_time = 0 if sleep_time < 0 else sleep_time
            sleep(sleep_time)
            start_time_2 = timeit.default_timer()
            while not self._queue.empty():
                data_list.append(self._queue.get())
            stop_time = timeit.default_timer()
            if len(data_list) > 0:
                # log.info('Data Scatter Count = {}'.format(len(data_list)))
                new_samples_array = np.concatenate(data_list)
                end_time_1 = stop_time - start_time_1 + self._time_index
                new_time_array = np.linspace(self._time_index, end_time_1, num=new_samples_array.shape[0])
                new_sample_sets = np.transpose(np.concatenate([[new_time_array], [new_samples_array]]))
                if self._samples_buffer is None:
                    self._samples_buffer = new_sample_sets
                else:
                    self._samples_buffer = np.concatenate([self._samples_buffer, new_sample_sets])
                # log.info('{}, {}'.format(str(self.time_index), str(end_time_1)))
                self._time_index = end_time_1
                self._master.mf.connection_p.top_left_f.set_samples_scatter(self._samples_buffer)
                self._x_adjustment(percent=20)
                self._y_adjustment()
            end_time_2 = timeit.default_timer()
            data_processing_time = end_time_2 - start_time_2
        log.info('ConnSamplesThread Closed')

    def _x_adjustment(self, percent):
        if self._time_index >= self._time_interval:
            shape = self._samples_buffer.shape[0]
            reduce_size = int(shape * (percent / 100))
            last_sample_time = self._samples_buffer[reduce_size][0]
            a = np.zeros(shape - reduce_size) + last_sample_time
            b = np.zeros(shape - reduce_size)
            ab = np.transpose(np.concatenate([[a], [b]]))
            self._samples_buffer = self._samples_buffer[reduce_size:]
            self._samples_buffer -= ab
            self._time_index = self._samples_buffer[-1][0]

    def _y_adjustment(self):
        samples_data = np.transpose(self._samples_buffer)[1]
        min_sample = samples_data.min()
        max_sample = samples_data.max()
        y_lim = list(self._master.mf.connection_p.top_left_f.get_samples_y_lim())
        new_y_lim = y_lim.copy()
        if min_sample - y_lim[0] > 5000 or y_lim[0] - min_sample > 5000:
            new_y_lim[0] = min_sample - 5000
        if max_sample > y_lim[1]:
            new_y_lim[1] = max_sample * 1.2
        if new_y_lim != y_lim:
            self._master.mf.connection_p.top_left_f.set_samples_y_limit(new_y_lim[0], new_y_lim[1])

    def set_thread_on(self):
        self._thread_on.set()

    def clear_thread_on(self):
        self._thread_on.clear()

    def resume_thread(self):
        self._thread_resume.set()

    def pause_thread(self):
        self._thread_resume.clear()

    def is_paused(self):
        return not self._thread_resume.is_set()

    def is_resume(self):
        return self._thread_resume.is_set()


class ConnDistance1Thread(Thread):
    def __init__(self, master: App, queue: Queue = None, update_freq: int = 1):
        super().__init__()
        self.daemon = True
        self._master = master
        self._queue = queue
        self._update_freq = update_freq
        self._update_period = 1 / self._update_freq
        self._time_interval = 10
        self._time_index = 0
        self._distance1_buffer = None
        self._full_scale = 0
        self._thread_on = Event()
        self._thread_on.clear()
        """ 
        self._thread_resume event shows the thread is paused or not.
        If the self._thread_resume is set, the thread is not pausing.
        If the self._thread_resume is not set, the thread is paused.
        """
        self._thread_resume = Event()
        self._thread_resume.set()

    def run(self):
        self._distance1_buffer = None
        data_processing_time = 0
        while self._thread_on.is_set():
            self._thread_resume.wait()
            data_list = []
            start_time_1 = timeit.default_timer()
            sleep_time = self._update_period - data_processing_time
            """ Remove sleep time if data processing time is longer than update_period """
            sleep_time = 0 if sleep_time < 0 else sleep_time
            sleep(sleep_time)
            start_time_2 = timeit.default_timer()
            # log.info('[ConnDist1Thread] Waiting for distance Queue to be filled...')
            while self._queue.empty() and self._thread_on.is_set():
                sleep(0.1)
            while not self._queue.empty():
                data_list.append(self._queue.get())
                # log.info('[ConnDist1Thread] Got distance from Queue')
            stop_time = timeit.default_timer()
            if len(data_list) > 0:
                # log.info('Data Scatter Count = {}'.format(len(data_list)))
                new_samples_array = np.concatenate(data_list)
                end_time_1 = stop_time - start_time_1 + self._time_index
                new_time_array = np.linspace(self._time_index, end_time_1, num=new_samples_array.shape[0])
                new_sample_sets = np.transpose(np.concatenate([[new_time_array], [new_samples_array]]))
                if self._distance1_buffer is None:
                    self._distance1_buffer = new_sample_sets
                else:
                    self._distance1_buffer = np.concatenate([self._distance1_buffer, new_sample_sets])
                # log.info('{}, {}'.format(str(self.time_index), str(end_time_1)))
                self._time_index = end_time_1
                self._master.mf.connection_p.bottom_left_f.set_samples_scatter(self._distance1_buffer)
                self._x_adjustment(percent=20)
                self._y_adjustment()
            end_time_2 = timeit.default_timer()
            data_processing_time = end_time_2 - start_time_2
        log.info('ConnDistance1Thread Closed')

    def _x_adjustment(self, percent):
        if self._time_index >= self._time_interval:
            shape = self._distance1_buffer.shape[0]
            reduce_size = int(shape * (percent / 100))
            last_sample_time = self._distance1_buffer[reduce_size][0]
            a = np.zeros(shape - reduce_size) + last_sample_time
            b = np.zeros(shape - reduce_size)
            ab = np.transpose(np.concatenate([[a], [b]]))
            self._distance1_buffer = self._distance1_buffer[reduce_size:]
            self._distance1_buffer -= ab
            self._time_index = self._distance1_buffer[-1][0]

    def _y_adjustment(self):
        samples_data = np.transpose(self._distance1_buffer)[1]
        min_sample = samples_data.min()
        max_sample = samples_data.max()
        amplitude = max_sample - min_sample
        y_lim = list(self._master.mf.connection_p.bottom_left_f.get_samples_y_lim())
        new_y_lim = y_lim.copy()
        if (min_sample - y_lim[0]) > (amplitude * 4) or y_lim[0] > min_sample:
            new_y_lim[0] = min_sample - amplitude * 1.5
        elif min_sample == 0:
            new_y_lim[0] = -20
        if max_sample > y_lim[1]:
            new_y_lim[1] = max_sample + amplitude
            if new_y_lim[1] > (self._full_scale + 10):
                new_y_lim[1] = self._full_scale + 10
        elif (y_lim[1] - max_sample) > amplitude * 2:
            new_y_lim[1] = max_sample + amplitude
        if new_y_lim != y_lim:
            self._master.mf.connection_p.bottom_left_f.set_samples_y_limit(new_y_lim[0], new_y_lim[1])

    def set_full_scale(self, val):
        self._full_scale = val

    def set_thread_on(self):
        self._thread_on.set()

    def clear_thread_on(self):
        self._thread_on.clear()

    def resume_thread(self):
        self._thread_resume.set()

    def pause_thread(self):
        self._thread_resume.clear()

    def is_paused(self):
        return not self._thread_resume.is_set()

    def is_resume(self):
        return self._thread_resume.is_set()


class TrigLostVerifyThread(Thread):
    def __init__(self, master: App, queue: Queue, update_freq: int = 10):
        super().__init__()
        global conn_cb
        self.daemon = True
        self._master = master
        self._queue = queue
        self._update_freq = update_freq
        self._update_period = 1 / self._update_freq
        self._conn_cb = conn_cb
        self._thread_on = Event()
        self._thread_on.clear()
        self.first_sample = None
        self._user_cancel = False
        self.axis_index = {'x': 1, 'y': 2, 'z': 3}
        self.data_buffer = []
        self.trigger_lost_position_list = []
        self.trigger_axis = ''
        self.exp_trigger_count = 0
        self.trigger_happened = 0
        self.shz = self._master.tf.sample_rate_led_f.get_tf_sample_rate()

    def run(self):
        self._master.mf.trigger_test_p.set_check_check_trigger_btn_text('Setting up')
        self._master.tf.output_signal_f.set_output_signal('65, 66, 67, 83, 16640, 16641')
        selected_mode = self._master.mf.trigger_test_p.right_f.get_tt_trig_mode_value()
        if selected_mode != self._conn_cb.mf_tt_tre:
            self._master.mf.trigger_test_p.right_f.set_tt_trig_mode_value(self._conn_cb.mf_tt_tre)
            self._conn_cb.trig_test_mode_select_cmd()
        is_use_encoder = self._master.mf.trigger_test_p.right_f.get_use_encoder_trig()
        if is_use_encoder == 0:
            self._master.mf.trigger_test_p.right_f.set_use_encoder_trig(1)
            self._conn_cb.use_encoder_trig_cmd()
        self._master.mf.trigger_test_p.right_f.tt_check_trigger_each_widgets_state()
        start_pos = int(self._master.mf.trigger_test_p.right_f.get_start_pos())
        interval = int(self._master.mf.trigger_test_p.right_f.get_interval())
        stop_pos = int(self._master.mf.trigger_test_p.right_f.get_stop_pos())
        self.exp_trigger_count = int((stop_pos - start_pos) / interval) + 1
        self._master.mf.trigger_test_p.set_trigger_count(str(self.exp_trigger_count))
        self._master.mf.trigger_test_p.clear_trigger_happened()
        self._master.mf.trigger_test_p.clear_trigger_lost_info()
        self._master.mf.trigger_test_p.set_check_check_trigger_btn_green()
        self._master.mf.trigger_test_p.set_check_check_trigger_btn_text('Sensor Receiving Trigger..')
        self._thread_on.set()
        while self._thread_on.is_set():
            sleep(self._update_period)
            data_list = []
            while self._queue.empty() and self._thread_on.is_set():
                sleep(0.1)
            while not self._queue.empty():
                data_list.append(self._queue.get())
            self.data_buffer.extend(data_list)
            if self._thread_on.is_set():
                encoder_list = data_list[-1]
                sample_cnt_list = encoder_list[0]
                last_encoder_x = encoder_list[1][-1]
                last_encoder_y = encoder_list[2][-1]
                last_encoder_z = encoder_list[3][-1]
                exposure_flags = [i[4] for i in data_list]

                self.trigger_axis = self._master.mf.trigger_test_p.right_f.get_tt_axis()
                if len(exposure_flags) > 0:
                    for i, data_sets in enumerate(data_list):
                        for j, data in enumerate(data_sets[4]):
                            is_trigger_lost = bool(data & (1 << 1))
                            is_trigger_delayed = bool(data & (1 << 2))
                            if is_trigger_lost:
                                lost_pos = data_list[i][self.axis_index[self.trigger_axis]][j] - interval
                                self.trigger_lost_position_list.append(lost_pos)
                            if is_trigger_delayed:
                                btn_state = self._master.mf.trigger_test_p.get_check_check_trigger_btn_color()
                                if btn_state == 'g':
                                    self._master.mf.trigger_test_p.set_check_check_trigger_btn_red()
                                    self._master.mf.trigger_test_p.set_check_check_trigger_btn_text('Trig too Fast!')
                            else:
                                btn_state = self._master.mf.trigger_test_p.get_check_check_trigger_btn_color()
                                if btn_state == 'r':
                                    self._master.mf.trigger_test_p.set_check_check_trigger_btn_green()
                                    self._master.mf.trigger_test_p.set_check_check_trigger_btn_text('Sensor Receiving'
                                                                                                    ' Trigger..')
                if sample_cnt_list is not None:
                    if self.first_sample is None:
                        self.first_sample = data_list[0][0][0]  # first sample count
                    self.trigger_happened = sample_cnt_list[-1] - self.first_sample + 1
                    self._master.mf.trigger_test_p.set_trigger_happened(self.trigger_happened)
                else:
                    log.error('No sample count data from samples')
                    break
                if last_encoder_x is not None:
                    self._master.mf.trigger_test_p.set_encoder_x_value(last_encoder_x)
                if last_encoder_y is not None:
                    self._master.mf.trigger_test_p.set_encoder_y_value(last_encoder_y)
                if last_encoder_z is not None:
                    self._master.mf.trigger_test_p.set_encoder_z_value(last_encoder_z)
                if self.trigger_axis == 'x':
                    if (last_encoder_x >= stop_pos) or (stop_pos - last_encoder_x < 2):
                        self._thread_on.clear()
                elif self.trigger_axis == 'y':
                    if (last_encoder_y >= stop_pos) or (stop_pos - last_encoder_y < 2):
                        self._thread_on.clear()
                elif self.trigger_axis == 'z':
                    if (last_encoder_z >= stop_pos) or (stop_pos - last_encoder_z < 2):
                        self._thread_on.clear()
        self._master.mf.trigger_test_p.set_check_check_trigger_btn_normal()
        self._master.mf.trigger_test_p.set_check_check_trigger_btn_text('Check Trigger Lost')
        if self._user_cancel:
            self._master.mf.trigger_test_p.set_trigger_lost_info('[User Cancel]\n', warning=True)
        txt = 'Trigger count should be = {}\n'.format(self.exp_trigger_count)
        self._master.mf.trigger_test_p.set_trigger_lost_info(txt)
        txt = 'Trigger happened = {}\n'.format(self.trigger_happened)
        self._master.mf.trigger_test_p.set_trigger_lost_info(txt)
        txt = 'Trigger Lost Count = {}\n'.format(self.exp_trigger_count - self.trigger_happened)
        self._master.mf.trigger_test_p.set_trigger_lost_info(txt)
        txt = 'Trigger Lost Position (encoder {}) = {}\n'.format(self.trigger_axis, self.trigger_lost_position_list)
        self._master.mf.trigger_test_p.set_trigger_lost_info(txt)
        self.save_results()
        log.info('TrigLostVerifyThread Closed')

    def save_results(self):
        date = datetime.now().strftime("%Y_%m_%d-%I%M%S")
        if not os.path.exists('TrigLostReport'):
            os.makedirs('TrigLostReport')
        with open('TrigLostReport\\' + date + '.csv', 'w') as f:
            f.write('Scan Rate: {}Hz\n'.format(self.shz))
            f.write('Trigger count should be = {}\n'.format(self.exp_trigger_count))
            f.write('Trigger happened = {}\n'.format(self.trigger_happened))
            f.write('Trigger Lost Count = {}\n'.format(self.exp_trigger_count - self.trigger_happened))
            f.write('"Trigger Lost Position (encoder {}) = {}"\n'.format(self.trigger_axis,
                                                                         self.trigger_lost_position_list))
            f.write('Trigger Lost Position Count: {}\n'.format(len(self.trigger_lost_position_list)))
            f.write('Sample Counter(ID:83), Encoder {}, Exp. Flags (ID:76), Distance 1 Int16 CH1(ID:16640)\n'
                    .format(self.trigger_axis))
            for i, sample_sets in enumerate(self.data_buffer):
                sample_count = len(self.data_buffer[i][0])
                for j in range(sample_count):
                    f.write(str(sample_sets[0][j]) + ',')
                    f.write(str(sample_sets[self.axis_index[self.trigger_axis]][j]) + ',')
                    f.write(str(sample_sets[4][j]) + ',')
                    f.write(str(sample_sets[5][j]) + '\n')

    def clear_thread_on(self):
        self._thread_on.clear()

    def user_cancel(self):
        self._user_cancel = True

    def trig_verify_thread_on(self):
        return self._thread_on.is_set()


class AsyncCommand(Thread):
    def __init__(self, master: MainGUI, cmd_rsp_handle: Callable):
        super().__init__()
        self.daemon = True
        self._master = master
        self.cmd_rsp_callback = cmd_rsp_handle
        self._queue = Queue()
        self._ip = None
        self._device_type = None
        self.async_conn = None
        self._conn_on = Event()
        self.query_cmd = None
        self.gui_update = False
        self.etr_cmds_index = []
        self._etr_to_etp_index = {
            0: 1,  # Start pos
            1: 2,  # Stop pos
            2: 3,  # Interval
            4: 4,  # On return
            5: 0,  # Axis
        }

    def run(self) -> None:
        try:
            with connection_from_params(addr=self._ip, conn_mode=OperationMode.ASYNC, device_type=self._device_type,
                                        resp_callback=self.gen_callback, data_callback=self.data_callback,
                                        async_auto_buffer=False) as self.async_conn:
                log.info('Async Connection On')
                while self._conn_on.is_set():
                    while self._queue.empty() and self._conn_on.is_set():
                        sleep(0.1)
                    while not self._queue.empty():
                        self.rsp_handle(rsp=self._queue.get())
                    sleep(1 / 32)

        except Exception or APIException as err:
            log.warning('Async Connection FAILED: {}'.format(err))
            return
        log.info('Async Connection (Thread) Closed')

    def conn(self, ip: str, device_type: DeviceType):
        self._ip = ip
        self._device_type = device_type
        self._conn_on.set()
        self.start()

    def disconn(self):
        self._ip = None
        self._device_type = None
        self._conn_on.clear()

    def rsp_handle(self, rsp):
        txt = '[Sensor] <<$'
        if rsp and (rsp.error_code == 0):
            trans = self.rsp_transform(rsp)
            if trans is not None:
                cmd_str = trans[0]
                rsp_args = trans[1]
            else:
                cmd_str = cmd_str_from_id(rsp.cmd_id).replace('%', '')
                rsp_args = rsp.args if len(rsp.args) > 0 else None
            if cmd_str is None:
                return
            if self.gui_update:
                self.update_gui(rsp)
            q_str = ''
            if self.query_cmd == cmd_str:
                self.query_cmd = None
                q_str = '?'
            if type(rsp_args) == list:
                arg_str = ''
                if rsp_args[0] is not None:
                    if type(rsp_args[0]) == list:
                        for args in rsp_args:
                            arg_str += '; '.join([str(i) for i in args])
                    else:
                        arg_str = '; '.join([str(i) for i in rsp_args])
            elif type(rsp_args) == float:
                arg_str = str(round(rsp_args, 5))
            elif not rsp_args:
                arg_str = ''
            else:
                arg_str = str(rsp_args)
            txt += (cmd_str + q_str + arg_str).replace('\00', '')
        else:
            txt += '<<Error in CMD!'
        self._master.cmd_f.insert_textbox(txt)

    def update_gui(self, rsp):
        cmd_str = cmd_str_from_id(rsp.cmd_id).replace('%', '')
        if cmd_str == 'SCA' and self.query_cmd == 'SCA':
            full_scale = rsp.args[0]
            self._master.lf.probe_sel_f.set_full_scale(' ' + str(full_scale))
            self._master.mf.focus_p.update_multichannel_profile_view_distance_y_lim(0, int(full_scale * 1.1))
            self.gui_update = False

    def rsp_transform(self, rsp: Response):
        """ Transform the CHRocodileLib Internal Commands to Device Commands and update parameters to GUI """
        cmd_str = cmd_str_from_id(rsp.cmd_id).replace('%', '')
        if cmd_str == 'TRM' and rsp.args[0] == 0:
            return 'CTN', None
        elif cmd_str == 'TRM' and rsp.args[0] == 1:
            return 'TRG', None
        elif cmd_str == 'TRM' and rsp.args[0] == 2:
            return 'TRE', None
        elif cmd_str == 'ETE':
            return 'ETR', [3, rsp.args[0]]
        elif cmd_str == 'ETP':
            index_match = False
            cmd_index = None
            for cmd_index in self.etr_cmds_index:
                if cmd_index in self._etr_to_etp_index.keys():
                    index_match = True
                    break
            if index_match and cmd_index is not None:
                self.etr_cmds_index.remove(cmd_index)
                return 'ETR', [cmd_index, rsp.args[self._etr_to_etp_index[cmd_index]]]
            if cmd_index == 7:
                return None, None
        elif cmd_str == 'EPS':
            return 'ENC', [rsp.args[0], rsp.args[1]]
        elif cmd_str == 'LAI':
            self._master.tf.sample_rate_led_f.set_tf_led('{:0.1f}'.format(rsp.args[0]))
        elif cmd_str == 'SHZ':
            self._master.tf.sample_rate_led_f.set_tf_sample_rate('{:0.0f}'.format(rsp.args[0]))
            self._master.mf.trigger_scan_p.top_left_f.forth_r_f.tc_dx_callback('')
            self.cmd_rsp_callback(cmd_str, rsp.args[0])
        elif cmd_str == 'NOP':
            self._master.lf.multilayer_stn_f.set_lf_number_of_peak(rsp.args[0])
        elif cmd_str == 'AVD':
            self._master.lf.average_f.set_data_sample(rsp.args[0])
        elif cmd_str == 'AVS':
            self._master.lf.average_f.set_spectrum_average(rsp.args[0])
        elif cmd_str == 'MESG':
            if 'closing connection' in rsp.args[3]:
                self.disconn()
            else:
                return None
        elif cmd_str == 'DRK':
            freq_str = ('{:0.2f}'.format(rsp.args[0]))
            self._master.lf.dark_ref_f.info_window(dark_type=0, freq=freq_str,
                                                   on_close_cmd=self._master.lf.dark_ref_f.enable_dark_button)
        elif cmd_str == 'FDK':
            freq_str = ('{:0.2f}'.format(rsp.args[0]))
            self._master.lf.dark_ref_f.info_window(dark_type=1, freq=freq_str,
                                                   on_close_cmd=self._master.lf.dark_ref_f.enable_fast_dark_button)
        elif cmd_str == 'SENX':
            rsp_string_list = [i[:-1] for i in rsp.args if i[3:6] == 'SNr']
            self._master.mf.init_p.set_initial_probe_info_textbox('\n'.join(rsp_string_list))
        else:
            return None

    def gen_callback(self, cb: Response):
        self._queue.put_nowait(cb)
        # print("Gen callback\n", cb)
        # if cb.args:
        #     print('First argument in response=', cb.args[0])

    def sodx_callback(self, cb: Response):
        pass

    def data_callback(self, cb: Data):
        pass


if __name__ == "__main__":
    app = App()
    log.info('Program Started')
    app.mainloop()
