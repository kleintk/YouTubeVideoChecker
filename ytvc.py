# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
import sys
import hauptfenster
import pickle
import os
import urllib.request
import xml.etree.ElementTree as ET
import webbrowser


class Hauptfenster(QMainWindow, hauptfenster.Ui_MainWindow):
    '''
    to do:
    '''

    ANZUSCHAUENDE_KANAELE_LISTE = []

    def __init__(self, parent=None):
        super(Hauptfenster, self).__init__(parent)
        self.setupUi(self)

        self.datenbankerstellen_fallsnichtvorhanden()
        self.kanaelerechtsanzeigen()
        self.stackedWidget.setCurrentWidget(self.page)
        self.label.hide()
        self.progressBar.reset()

        self.pushButtonHinzufuegen.clicked.connect(self.kanalhinzufuegen)
        self.pushButtonLoeschen.clicked.connect(self.kanalloeschen)
        self.pushButtonOeffnen.clicked.connect(self.oeffnen)
        self.pushButtonPruefen.clicked.connect(self.pruefen)
        self.actionPruefen.triggered.connect(self.pruefen)
        self.actionInfo.triggered.connect(self.info)
        self.actionBeenden.triggered.connect(self.programmbeenden)

        self.schuftet = PruefenThread()
        self.schuftet.start_signal.connect(self.startsignalemited)
        self.schuftet.status_signal[int].connect(self.statussignalemited)
        self.schuftet.ende_signal[int].connect(self.endesignalemited)
        self.schuftet.kanal_signal[str].connect(self.kanalsignalemited)

    def datenbankerstellen_fallsnichtvorhanden(self):
        if os.path.exists('datenbank.db'):
            pass
        else:
            datei = open('datenbank.db', 'wb')
            meineliste = [["SemperVideo", ""]]
            pickle.dump(meineliste, datei)
            datei.close()

    def datenbanksicheroeffnen(self):
        if os.path.exists('datenbank.db'):
            try:
                datei = open('datenbank.db', 'rb')
                meine_kanal_liste = pickle.load(datei)
                #[['kanalname', '*** titelDesLetztenVideos ***'],...]
                datei.close()
                return meine_kanal_liste
            except:
                self.statusbar.showMessage("Fehler beim Laden der Datenbank", 3000)
        else:
            self.statusbar.showMessage("Keine Datenbank gefunden.", 3000)

    def datenbanksicherspeichern(self, meine_kanal_liste):
        if os.path.exists('datenbank.db'):
            try:
                datei = open('datenbank.db', 'wb')
                pickle.dump(meine_kanal_liste, datei)
                datei.close()
            except:
                self.statusbar.showMessage("Fehler beim Speichern der Datenbank", 3000)
        else:
            self.statusbar.showMessage("Keine Datenbank gefunden.", 3000)

    def kanaelerechtsanzeigen(self):
        meine_kanal_liste = self.datenbanksicheroeffnen()
        self.listWidgetKanaeleRechts.clear()
        for kanal in meine_kanal_liste:
            self.listWidgetKanaeleRechts.addItem(kanal[0])

    def kanalhinzufuegen(self):
        kanal_name = self.lineEditKanalname.text()
        antwort = self.anfrage_an_youtube_server(
            "https://gdata.youtube.com/feeds/api/users/" + str(kanal_name) + "/uploads")
        if antwort == 5:
            self.statusbar.clearMessage()
            self.statusbar.showMessage("Kanal nicht gefunden.", 5000)
            self.lineEditKanalname.clear()
        else:
            temp_liste = [kanal_name, ""]
            meine_kanal_liste = self.datenbanksicheroeffnen()
            meine_kanal_liste.append(temp_liste)
            self.datenbanksicherspeichern(meine_kanal_liste)
            self.lineEditKanalname.clear()
            self.kanaelerechtsanzeigen()

    def kanalloeschen(self):
        kanalitem = self.listWidgetKanaeleRechts.currentItem()
        kanalname = kanalitem.text()
        meine_kanal_liste = self.datenbanksicheroeffnen()
        for teilliste in meine_kanal_liste:
            if teilliste[0] == kanalname:
                meine_kanal_liste.pop(meine_kanal_liste.index(teilliste))
                break
        self.datenbanksicherspeichern(meine_kanal_liste)
        self.kanaelerechtsanzeigen()

    def anfrage_an_youtube_server(self, anfrage_url):
        try:
            f = urllib.request.urlopen(anfrage_url)
            antwort = f.read().decode(sys.stdout.encoding, 'utf-8')
            f.close()
            return antwort
        except:
            self.statusbar.showMessage("Fehler beim Verbinden mit YouTube.", 3000)
            return 5

    def video_infos_abfragen(self, nutzer_kanal_name, anzahl_videos):
        antwort = self.anfrage_an_youtube_server(
            "https://gdata.youtube.com/feeds/api/users/" + str(nutzer_kanal_name) + "/uploads")
        root = ET.fromstring(antwort)
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        entries = entries[:anzahl_videos]  # nur die neuesten 10 Eintraege
        entries.reverse()  # der neueste eintrag steht konsolen-freundlich unten

        ergebnis = []
        for entry in entries:
            # Titel finden
            titel = "*** " + entry.find('{http://www.w3.org/2005/Atom}title').text + " ***"

            # Erscheinungsdatum finden
            erscheinungsdatum = entry.find('{http://www.w3.org/2005/Atom}published').text
            erscheinungsdatum = erscheinungsdatum.replace("-", ".")
            erscheinungsdatum = erscheinungsdatum.replace("T", "   ")
            abschneiden = erscheinungsdatum.find("Z")
            erscheinungsdatum = erscheinungsdatum[:abschneiden - 7]  # doofes datums-format editieren

            # Beschreibung finden
            #beschreibung = entry.find('{http://www.w3.org/2005/Atom}content').text
            #abschneiden = beschreibung.find("Vielen Dank")
            #beschreibung = beschreibung[:abschneiden-2]  # Dankes-Hymnen wegschneiden

            # Link auf Youtube finden
            all_links = entry.findall("{http://www.w3.org/2005/Atom}link")
            link = all_links[0].attrib['href']  # sollte immer der richtige ref link sein (pruefen!)

            teilliste = [titel, erscheinungsdatum, link]
            #teilliste.append(beschreibung)

            ergebnis.append(teilliste)

        return ergebnis

    def pruefen(self):
        self.schuftet.start()

    def oeffnen(self):
        kanal_item = self.listWidgetErgebnis.currentItem()
        kanal_name = kanal_item.text()
        webbrowser.open_new_tab("http://www.youtube.com/user/" + kanal_name + "/videos")
        self.listWidgetErgebnis.removeItemWidget(kanal_item)
        self.listWidgetErgebnis.clear()
        self.ANZUSCHAUENDE_KANAELE_LISTE.pop(self.ANZUSCHAUENDE_KANAELE_LISTE.index(kanal_name))
        for kanal in self.ANZUSCHAUENDE_KANAELE_LISTE:
            self.listWidgetErgebnis.addItem(kanal)
        if len(self.ANZUSCHAUENDE_KANAELE_LISTE) == 0:
            self.stackedWidget.setCurrentWidget(self.page)

    def info(self):
        QMessageBox.information(self, "YouTubeVideoChecker!", "Coded by Tkinter/Phate")

    def programmbeenden(self):
        sys.exit()

    def startsignalemited(self):
        self.stackedWidget.setCurrentWidget(self.page_2)

    def statussignalemited(self, prozent):
        self.progressBar.setValue(prozent)

    def endesignalemited(self, erg):
        self.schuftet.terminate()
        if erg == 1:
            self.stackedWidget.setCurrentWidget(form.page_3)
        if erg == 0:
            self.stackedWidget.setCurrentWidget(form.page)
            self.label.show()

    def kanalsignalemited(self, kanal):
        self.listWidgetErgebnis.addItem(kanal)


class PruefenThread(QThread):
    start_signal = Signal()
    status_signal = Signal(int)
    kanal_signal = Signal(str)
    ende_signal = Signal(int)

    def __init__(self, parent=None):
        super(PruefenThread, self).__init__(parent)

    def run(self):
        self.start_signal.emit()

        meine_liste = form.datenbanksicheroeffnen()
        ausgabe_liste = []
        neue_vids = False
        anschauen = False

        # ueberpruefung ob neue videos vorhanden sind
        sts = 0
        for kanal in meine_liste:
            sts += 100 / len(meine_liste)
            self.status_signal.emit(sts)
            ergebnisliste = form.video_infos_abfragen(kanal[0], 10)  # [[titel, erscheinungsDatum, link],...]

            aktueller_kanalname = kanal[0]
            bisher_neuestes_video = kanal[1]
            temp_neuestes_video = ""

            for item in ergebnisliste:
                anschauen = False
                aktuell_zu_pruefendes_video = item[0]
                if aktuell_zu_pruefendes_video != bisher_neuestes_video:
                    temp_neuestes_video = aktuell_zu_pruefendes_video
                    anschauen = True

                else:
                    anschauen = False
            if anschauen:
                neue_vids = True
                ausgabe_liste.append(aktueller_kanalname)
                kanal[1] = temp_neuestes_video

            else:
                # es gibt keine neuen Videos
                pass

        # aenderungen speichern
        form.datenbanksicherspeichern(meine_liste)

        if neue_vids:

            for url in ausgabe_liste:
                form.ANZUSCHAUENDE_KANAELE_LISTE.append(url)
                self.kanal_signal.emit(url)

            self.ende_signal.emit(1)

        if not neue_vids:
            self.ende_signal.emit(0)


app = QApplication(sys.argv)
form = Hauptfenster()
form.show()
app.exec_()