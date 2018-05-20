# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              Asistente LADM_COL
                             --------------------
        begin                : 2018-04-30
        git sha              : :%H$
        copyright            : (C) 2018 by Germán Carrillo (BSF Swissphoto)
        email                : gcarrillo@linuxmail.org
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
from ..utils import get_ui_class
from ..utils import qgis_utils

import os
import glob
import shutil
import zipfile
import tempfile
from functools import partial

from qgis.core import QgsNetworkContentFetcherTask, QgsApplication, Qgis
from qgis.PyQt.QtCore import (
    QUrl,
    QFile,
    QIODevice,
    QCoreApplication,
    QLocale,
    QSettings
)
from qgis.PyQt.QtWidgets import QDialog, QSizePolicy, QGridLayout

from ..config.general_config import (
    PLUGIN_VERSION,
    HELP_DOWNLOAD,
    PLUGIN_NAME
)

DIALOG_UI = get_ui_class('about_dialog.ui')

class AboutDialog(QDialog, DIALOG_UI):
    def __init__(self, qgis_utils):
        QDialog.__init__(self)
        self.setupUi(self)
        self.qgis_utils = qgis_utils
        self.os_language = QLocale(QSettings().value('locale/userLocale')).name()[:2]
        self.help_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), 'python', 'plugins', 'asistente_ladm_col', 'help')
        self.check_local_help()

    def check_local_help(self):
        try:
            self.btn_download_help.clicked.disconnect(self.show_help)
        except TypeError as e:
            pass
        try:
            self.btn_download_help.clicked.disconnect(self.download_help)
        except TypeError as e:
            pass

        if os.path.exists(os.path.join(self.help_dir,
                                       self.os_language,
                                       'index.html')):
            self.btn_download_help.setText(QCoreApplication.translate("AboutDialog", 'Open help from local folder'))
            self.btn_download_help.clicked.connect(self.show_help)
        else:
            self.btn_download_help.setText(QCoreApplication.translate("AboutDialog", 'Download help for offline access'))
            self.btn_download_help.clicked.connect(self.download_help)

    def save_file(self, fetcher_task):
        if fetcher_task.reply() is not None:
            tmpFile = tempfile.mktemp()
            tmpFold = tempfile.mktemp()
            outFile = QFile(tmpFile)
            outFile.open(QIODevice.WriteOnly)
            outFile.write(fetcher_task.reply().readAll())
            outFile.close()

            try:
                with zipfile.ZipFile(tmpFile, "r") as zip_ref:
                    zip_ref.extractall(tmpFold)
                    languages = glob.glob(os.path.join(tmpFold, 'asistente_ladm_col_docs/*'))

                    for language in languages:
                        shutil.move(language, os.path.join(self.help_dir, language[-2:]))

            except zipfile.BadZipFile as e:
                self.qgis_utils.message_emitted.emit(
                    QCoreApplication.translate("AboutDialog", "There was an error with the download. The downloaded file is invalid."),
                    Qgis.Warning)

            self.qgis_utils.message_emitted.emit(
                QCoreApplication.translate("AboutDialog", "Help fiels were successfully downloaded and can be accessed offline from the About dialog!"),
                Qgis.Info)

        self.check_local_help()

    def download_help(self):
        self.btn_download_help.setEnabled(False)
        url = '/'.join([HELP_DOWNLOAD, PLUGIN_VERSION, 'asistente_ladm_col_docs.zip'])
        fetcher_task = QgsNetworkContentFetcherTask(QUrl(url))
        fetcher_task.fetched.connect(partial(self.save_file, fetcher_task))
        fetcher_task.taskCompleted.connect(self.enable_download_button)

    def enable_download_button(self):
        self.btn_download_help.setEnabled(True)
        self.check_local_help()

    def show_help(self):
        self.qgis_utils.show_help('')
