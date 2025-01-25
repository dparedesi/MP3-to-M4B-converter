import sys
import os
import subprocess
import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QAbstractItemView, QMenu, QGroupBox, QLineEdit,
    QProgressBar, QMessageBox, QGridLayout, QHeaderView, QCheckBox,
    QSizePolicy, QStatusBar
)

from PIL import Image, ImageQt
from version import __version__

def get_downloads_folder():
    """Return the user's Downloads folder cross‐platform."""
    home = os.path.expanduser("~")
    return os.path.join(home, "Downloads")

class ToggleSwitch(QCheckBox):
    """
    A QCheckBox that is styled to look like a toggle (pure QSS, no image files).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setChecked(False)
        self.setText("")


class CoverArtWidget(QWidget):
    """
    A custom widget with a dashed, rounded rectangle border,
    plus an arrow icon, 'Upload Cover' text, and a sub‐label.
    """
    def __init__(self, parent=None, size=400):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAcceptDrops(True)
        self.cover_path = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Arrow icon
        self.icon_label = QLabel()
        icon_pix = QPixmap(64, 64)
        icon_pix.fill(Qt.transparent)
        from PySide6.QtGui import QPainter, QPen, QColor
        painter = QPainter(icon_pix)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#4A90E2"), 6)
        painter.setPen(pen)
        # draw an up arrow
        painter.drawLine(32, 48, 32, 16)
        painter.drawLine(32, 16, 16, 32)
        painter.drawLine(32, 16, 48, 32)
        painter.end()
        self.icon_label.setPixmap(icon_pix)
        layout.addWidget(self.icon_label, alignment=Qt.AlignHCenter)

        # Title
        self.title_label = QLabel("Upload Cover")
        self.title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self.title_label)

        # Subtext
        self.subtext_label = QLabel(
            "Drag and drop or <span style='color:#007AFF; font-weight:bold;'>click</span> to browse<br><br>"
            "Supported file types: PNG, JPG, JPEG"
        )
        self.subtext_label.setAlignment(Qt.AlignCenter)
        self.subtext_label.setWordWrap(True)
        self.subtext_label.setStyleSheet("font-size: 11pt; color: #AAAAAA;")
        layout.addWidget(self.subtext_label)

    def paintEvent(self, event):
        super().paintEvent(event)
        from PySide6.QtGui import QPainter, QPen, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#5A5A5A"), 2, Qt.DashLine)
        painter.setPen(pen)
        rect = self.rect().adjusted(3, 3, -3, -3)
        painter.drawRoundedRect(rect, 10, 10)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.select_cover_image()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                fname = urls[0].toLocalFile()
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                fname = urls[0].toLocalFile()
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.set_cover_image(fname)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)

    def select_cover_image(self):
        dlg = QFileDialog()
        dlg.setNameFilters(["Image files (*.png *.jpg *.jpeg)"])
        if dlg.exec():
            files = dlg.selectedFiles()
            if files:
                self.set_cover_image(files[0])

    def set_cover_image(self, path):
        try:
            self.cover_path = path
            image = Image.open(path)
            from PIL.ImageQt import ImageQt
            qimage = ImageQt(image)
            pixmap = QPixmap.fromImage(qimage)

            scaled = pixmap.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            if not hasattr(self, "_cover_label"):
                self._cover_label = QLabel(self)
                self._cover_label.setAlignment(Qt.AlignCenter)
                self.layout().addWidget(self._cover_label)

            self._cover_label.setPixmap(scaled)
            # Hide placeholders
            self.icon_label.hide()
            self.title_label.hide()
            self.subtext_label.hide()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Couldn't load cover image:\n{str(e)}")

    def clear_cover(self):
        self.cover_path = None
        if hasattr(self, "_cover_label"):
            self.layout().removeWidget(self._cover_label)
            self._cover_label.deleteLater()
            del self._cover_label
        # Show placeholders again
        self.icon_label.show()
        self.title_label.show()
        self.subtext_label.show()
        self.update()


class M4BFusionPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"M4BFusion Pro v{__version__}")
        # Slightly smaller bottom margin to lift the progress bar
        self.setGeometry(100, 100, 1200, 780)

        self.chapters = []
        self.output_folder = None

        # Main widget + layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 10)  # bottom=10 to move bar slightly up
        main_layout.setSpacing(20)

        # Left panel
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel, stretch=2)

        # Right panel
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, stretch=1)

        self.init_left_panel(left_panel)
        self.init_right_panel(right_panel)

        # Status bar with a wide progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        # Let it stretch across the entire bottom
        self.statusBar().addPermanentWidget(self.progress_bar, 1)

        self.set_dark_stylesheet()

    def set_dark_stylesheet(self):
        """
        Dark theme + big round buttons + QCheckBox toggle styling + wide progress bar.
        """
        qss = """
        QMainWindow {
            background-color: #2E2E2E;
        }
        QWidget {
            background-color: #2E2E2E;
            color: #FFFFFF;
            font-size: 11pt;
        }
        QGroupBox {
            border: 1px solid #4A4A4A;
            margin-top: 6px;
            background-color: #2E2E2E;
            border-radius: 8px;
        }
        QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
            color: #CCCCCC;
            font-weight: bold;
        }
        QTableWidget {
            background-color: #1F1F1F;
            gridline-color: #3A3A3A;
            selection-background-color: #444444;
        }
        QTableWidget::item {
            color: #FFFFFF;
        }
        QHeaderView::section {
            background-color: #3A3A3A;
            color: #C0C0C0;
            font-weight: bold;
            padding: 5px;
            border: none;
        }
        QPushButton {
            background-color: #3A3A3A;
            color: #FFFFFF;
            border: none;
            border-radius: 24px;
            font-size: 12pt;
            font-weight: bold;
            padding: 10px 24px;
            min-width: 130px; /* make them equally wide */
            min-height: 40px;
        }
        QPushButton:hover {
            background-color: #4A4A4A;
        }
        QPushButton#primaryButton {
            background-color: #007AFF;
        }
        QPushButton#primaryButton:hover {
            background-color: #005BBB;
        }
        QLineEdit {
            background-color: #1F1F1F;
            border: 1px solid #4A4A4A;
            color: #FFFFFF;
            border-radius: 4px;
            padding: 4px;
        }
        QProgressBar {
            border: 1px solid #4A4A4A;
            text-align: center;
            color: #FFFFFF;
        }
        QProgressBar::chunk {
            background-color: #007AFF;
        }
        /* Pill-style toggle with QSS (no images). */
        QCheckBox::indicator {
            width: 50px;
            height: 28px;
        }
        QCheckBox::indicator:unchecked {
            border-radius: 14px;
            background-color: #777777;
        }
        QCheckBox::indicator:unchecked:hover {
            background-color: #888888;
        }
        QCheckBox::indicator:checked {
            border-radius: 14px;
            background-color: #007AFF;
        }
        QCheckBox::indicator:checked:hover {
            background-color: #005BBB;
        }
        """
        self.setStyleSheet(qss)

    def init_left_panel(self, layout: QVBoxLayout):
        # Button row
        btn_row = QHBoxLayout()
        layout.addLayout(btn_row)

        self.btn_add_media = QPushButton("+ Add Media")
        self.btn_add_media.clicked.connect(self.on_add_media)
        btn_row.addWidget(self.btn_add_media)

        self.btn_clear_all = QPushButton("Clear All")
        self.btn_clear_all.clicked.connect(self.on_clear_all)
        btn_row.addWidget(self.btn_clear_all)

        self.up_button = QPushButton("↑ Up")
        self.up_button.clicked.connect(self.on_move_up)
        self.up_button.setEnabled(False)
        btn_row.addWidget(self.up_button)

        self.down_button = QPushButton("↓ Down")
        self.down_button.clicked.connect(self.on_move_down)
        self.down_button.setEnabled(False)
        btn_row.addWidget(self.down_button)

        # Table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["File/chapter name", "Duration"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.table.itemSelectionChanged.connect(self.toggle_up_down_buttons)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_table_context_menu)

        layout.addWidget(self.table, stretch=1)

    def init_right_panel(self, layout: QVBoxLayout):
        # Cover art
        cover_group = QGroupBox("Cover Art")
        cover_layout = QVBoxLayout(cover_group)
        layout.addWidget(cover_group)

        self.cover_widget = CoverArtWidget(size=400)
        cover_layout.addWidget(self.cover_widget)

        # Metadata
        meta_group = QGroupBox("Book Metadata")
        meta_layout = QGridLayout(meta_group)
        layout.addWidget(meta_group)

        lbl_title = QLabel("Title:")
        meta_layout.addWidget(lbl_title, 0, 0, Qt.AlignLeft)
        self.txt_title = QLineEdit()
        meta_layout.addWidget(self.txt_title, 0, 1)

        lbl_author = QLabel("Author:")
        meta_layout.addWidget(lbl_author, 1, 0, Qt.AlignLeft)
        self.txt_author = QLineEdit()
        meta_layout.addWidget(self.txt_author, 1, 1)

        meta_layout.setColumnStretch(1, 1)

        # Merge row
        merge_layout = QHBoxLayout()
        lbl_merge = QLabel("Merge files, omitting files/chapter names:")
        self.toggle_merge = ToggleSwitch()
        merge_layout.addWidget(lbl_merge)
        merge_layout.addWidget(self.toggle_merge)
        merge_layout.addStretch(1)
        layout.addLayout(merge_layout)

        # Output row
        output_row = QHBoxLayout()
        layout.addLayout(output_row)

        self.btn_save_to = QPushButton("Save To…")
        self.btn_save_to.clicked.connect(self.on_select_output)
        # Let both fill horizontally so they match in size
        self.btn_save_to.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output_row.addWidget(self.btn_save_to)

        self.btn_convert = QPushButton("Convert")
        self.btn_convert.setObjectName("primaryButton")
        self.btn_convert.clicked.connect(self.on_convert)
        self.btn_convert.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output_row.addWidget(self.btn_convert)

        layout.addStretch(1)

    # -------------------------------------------------------------
    #  CHAPTERS
    # -------------------------------------------------------------
    def on_add_media(self):
        dlg = QFileDialog(self)
        dlg.setNameFilters(["Audio files (*.mp3 *.wav *.flac)", "All files (*.*)"])
        dlg.setFileMode(QFileDialog.ExistingFiles)
        if dlg.exec():
            files = dlg.selectedFiles()
            added = 0
            for f in files:
                if f.lower().endswith(".mp3"):
                    self.add_chapter(f)
                    added += 1

    def on_clear_all(self):
        self.chapters = []
        self.refresh_table()
        self.toggle_up_down_buttons()

    def add_chapter(self, file_path):
        try:
            duration = self.get_duration(file_path)
            base = os.path.splitext(os.path.basename(file_path))[0]
            self.chapters.append({
                "path": file_path,
                "name": base,
                "duration": duration
            })
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Couldn't add file:\n{str(e)}")

    def refresh_table(self):
        self.table.setRowCount(len(self.chapters))
        for i, ch in enumerate(self.chapters):
            name_item = QTableWidgetItem(ch["name"])
            duration_item = QTableWidgetItem(self.format_duration(ch["duration"]))
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, duration_item)

    def on_table_context_menu(self, pos):
        row_index = self.table.currentRow()
        if row_index < 0:
            return
        menu = QMenu(self)
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.on_delete_selected)
        menu.addAction(delete_action)
        menu.exec(self.table.mapToGlobal(pos))

    def on_delete_selected(self):
        selected = self.table.selectionModel().selectedRows()
        indices = sorted([r.row() for r in selected], reverse=True)
        for idx in indices:
            del self.chapters[idx]
        self.refresh_table()
        self.toggle_up_down_buttons()

    def toggle_up_down_buttons(self):
        sel = self.table.selectionModel().selectedRows()
        has_sel = bool(sel)
        self.up_button.setEnabled(has_sel)
        self.down_button.setEnabled(has_sel)

    def on_move_up(self):
        sel = [r.row() for r in self.table.selectionModel().selectedRows()]
        if not sel:
            return
        for row in sel:
            if row > 0:
                self.chapters[row], self.chapters[row - 1] = self.chapters[row - 1], self.chapters[row]
        self.refresh_table()
        for row in sel:
            self.table.selectRow(max(row - 1, 0))

    def on_move_down(self):
        sel = [r.row() for r in self.table.selectionModel().selectedRows()]
        if not sel:
            return
        for row in reversed(sel):
            if row < len(self.chapters) - 1:
                self.chapters[row], self.chapters[row + 1] = self.chapters[row + 1], self.chapters[row]
        self.refresh_table()
        for row in sel:
            self.table.selectRow(min(row + 1, len(self.chapters) - 1))

    # -------------------------------------------------------------
    #  OUTPUT / CONVERSION
    # -------------------------------------------------------------
    def on_select_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder

    def on_convert(self):
        # Default to Downloads if no folder chosen
        if not self.output_folder:
            self.output_folder = get_downloads_folder()

        if not self.validate_inputs():
            return

        self.set_ui_enabled(False)
        try:
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            self.run_conversion()

            QMessageBox.information(self, "Success", "Conversion completed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.set_ui_enabled(True)

    def validate_inputs(self):
        errors = []
        if not self.chapters:
            errors.append("Please add at least one MP3 file.")
        if not self.txt_title.text().strip():
            errors.append("Please enter a title.")
        if not self.txt_author.text().strip():
            errors.append("Please enter an author.")
        if errors:
            QMessageBox.critical(self, "Validation Error", "\n".join(errors))
            return False
        return True

    def set_ui_enabled(self, enabled):
        self.table.setEnabled(enabled)
        self.txt_title.setEnabled(enabled)
        self.txt_author.setEnabled(enabled)
        self.btn_save_to.setEnabled(enabled)
        self.btn_convert.setEnabled(enabled)
        self.toggle_merge.setEnabled(enabled)
        self.setCursor(Qt.WaitCursor if not enabled else Qt.ArrowCursor)

    def run_conversion(self):
        merge_files = self.toggle_merge.isChecked()
        filelist_path = os.path.join(self.output_folder, "filelist.txt")
        metadata_path = os.path.join(self.output_folder, "metadata.txt")
        cover_temp = os.path.join(self.output_folder, "temp_cover.jpg")

        # Write file list
        with open(filelist_path, "w") as f:
            for ch in self.chapters:
                f.write(f"file '{ch['path']}'\n")

        cover_path = None
        if self.cover_widget.cover_path:
            cover_path = cover_temp
            self.process_cover_image(self.cover_widget.cover_path, cover_temp)

        out_file = os.path.join(
            self.output_folder,
            f"{self.txt_title.text().strip()}.m4b"
        )

        if merge_files:
            # Merge into one single track
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", filelist_path
            ]
            if cover_path:
                cmd += ["-i", cover_path]

            cmd += [
                "-map", "0:a",
                "-c:a", "aac", "-b:a", "128k",
                "-metadata", f"title={self.txt_title.text().strip()}",
                "-metadata", f"artist={self.txt_author.text().strip()}"
            ]
            if cover_path:
                cmd += [
                    "-map", "1:v",
                    "-c:v", "copy",
                    "-disposition:v", "attached_pic"
                ]
            cmd.append(out_file)
        else:
            # Multiple chapters
            self.create_ffmetadata(metadata_path)
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", filelist_path,
                "-i", metadata_path
            ]
            if cover_path:
                cmd += ["-i", cover_path]
            cmd += [
                "-map_metadata", "1",
                "-map", "0:a",
                "-c:a", "aac", "-b:a", "128k",
                "-metadata", f"title={self.txt_title.text().strip()}",
                "-metadata", f"artist={self.txt_author.text().strip()}"
            ]
            if cover_path:
                cmd += [
                    "-map", "2:v",
                    "-c:v", "copy",
                    "-disposition:v", "attached_pic"
                ]
            cmd.append(out_file)

        self.ffmpeg_run(cmd)
        # Clean up
        for f in [filelist_path, metadata_path, cover_temp]:
            if os.path.exists(f):
                os.remove(f)
        self.progress_bar.setValue(100)

    def ffmpeg_run(self, cmd):
        total_sec = sum(ch["duration"] for ch in self.chapters)
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)

        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if "time=" in line:
                time_str = line.split("time=")[1].split()[0]
                current_sec = self.time_to_seconds(time_str)
                pct = (current_sec / total_sec) * 100 if total_sec > 0 else 0
                self.progress_bar.setValue(int(pct))
                QApplication.processEvents()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)

    def process_cover_image(self, src, dest):
        cmd = [
            "ffmpeg", "-y",
            "-i", src,
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuvj420p",
            "-q:v", "2", "-frames:v", "1",
            dest
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def create_ffmetadata(self, metadata_path):
        with open(metadata_path, "w") as f:
            f.write(";FFMETADATA1\n")
            current_time = 0.0
            for c in self.chapters:
                end_time = current_time + c["duration"]
                f.write(
                    f"[CHAPTER]\n"
                    f"TIMEBASE=1/1000\n"
                    f"START={int(current_time * 1000)}\n"
                    f"END={int(end_time * 1000)}\n"
                    f"title={c['name']}\n\n"
                )
                current_time = end_time

    # -------------------------------------------------------------
    #  UTILS
    # -------------------------------------------------------------
    def get_duration(self, path: str) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Couldn't get duration for {os.path.basename(path)}")
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])

    def format_duration(self, secs: float) -> str:
        hrs = int(secs // 3600)
        mins = int((secs % 3600) // 60)
        s = int(secs % 60)
        return f"{hrs:02d}:{mins:02d}:{s:02d}"

    def time_to_seconds(self, time_str: str) -> float:
        parts = time_str.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return float(h)*3600 + float(m)*60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return float(m)*60 + float(s)
        return float(parts[0])


def main():
    app = QApplication(sys.argv)

    # Set application icon
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "resources", "app_icon.icns")
    
    if not os.path.exists(icon_path):
        QMessageBox.critical(None, "Error", f"Icon file not found at {icon_path}")
    else:
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    window = M4BFusionPro()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
