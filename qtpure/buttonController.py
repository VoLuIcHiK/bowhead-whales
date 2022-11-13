import os.path
from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QTableWidgetItem, \
    QHeaderView

from .backend import *
from .design_second import Ui_MainWindow


def main_function(path, new_window, ui_window: Ui_MainWindow):
    mode = '1'
    for file in os.listdir(path):
        if os.path.isdir(os.path.join(path, file)):
            mode = '2'
            break
    th1 = None
    if mode == '1':
        '''вызываем функцию для случая когда кит один'''
        th1 = threading.Thread(target=parse_all_images_in_folder_recursivily,
                               args=(path,),
                               daemon=True)
        th1.start()
        th1.join(0.02)
    else:
        '''вызываем функцию для случая когда китов много'''
        th1 = threading.Thread(target=parse_inner_folders_as_groups,
                               args=(path,),
                               daemon=True)
        th1.start()
        th1.join(0.02)
    ui_window.status.setText("Статус выполнения: обработка...")

    table = ui_window.tableWidget
    table.setColumnCount(2)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(
        QHeaderView.Stretch)
    new_window.show()

    def local_func_one_folder():
        nonlocal th1, table
        table.setHorizontalHeaderLabels(["ID кита", "Кол-во изображений"])
        table.verticalHeader().setVisible(False)
        total = 0
        new_entity = 0
        last_pass = False
        entity_storage = dict()
        current_row = -1
        while True:
            sleep(0.5)
            # key = название папки
            # value - словарь номеров китов и кол-ва файлов с ними
            for key, value in get_only_stats_from_new_parsed_images().items():
                for key2, value2 in value.items():
                    if key2 not in entity_storage:
                        current_row += 1
                        entity_storage.update({key2: [value2, current_row]})
                        table.insertRow(current_row)
                        x = QTableWidgetItem(str(key2))
                        x.setTextAlignment(Qt.AlignCenter)
                        table.setItem(current_row, 0,
                                      x)
                        y = QTableWidgetItem(
                            str(entity_storage[key2][0]))
                        y.setTextAlignment(Qt.AlignCenter)
                        table.setItem(current_row, 1, y)
                    else:
                        entity_storage[key2][0] += value2
                        x = QTableWidgetItem(
                            str(entity_storage[key2][0]))
                        x.setTextAlignment(Qt.AlignCenter)
                        table.setItem(entity_storage[key2][1], 1,
                                      x)
                    table.setHidden(True)
                    table.setHidden(False)
                    new_window.setFocus()
                    total += value2
                    if key2 == 0:
                        new_entity += value2
                ui_window.pics_count.setText(
                    "Количество обработанных картинок: " + str(total))
                ui_window.new_count.setText(
                    "Количество изображений новых особей: " + str(new_entity))

            if th1.is_alive():
                continue
            if last_pass:
                break
            last_pass = True
        ui_window.status.setText("Статус выполнения: завершено!")
        f = open('../results.csv', mode="w+", encoding='utf8')
        f.write("ID;quanity\n")
        for i in range(table.rowCount()):
            f.write(
                f"{table.item(i, 0).text()};{table.item(i, 1).text()}\n")
        f.close()

    def local_func_recur():
        nonlocal th1, table
        table.setHorizontalHeaderLabels(["Название папки", "ID кита"])
        table.verticalHeader().setVisible(False)
        total = 0
        new_entity = 0
        last_pass = False
        current_row = -1
        entity_storage = dict()
        while True:
            sleep(0.5)
            for key, value in get_only_stats_from_new_parsed_images().items():
                if key not in entity_storage:
                    current_row += 1
                    local_new = 0
                    local_old = 0
                    ent_id = ""
                    entity_storage.update(
                        {key: [current_row, local_new, local_old, '0']})
                else:
                    local_new = entity_storage[key][1]
                    local_old = entity_storage[key][2]
                    ent_id = entity_storage[key][3]
                for key2, value2 in value.items():
                    if key2 == 0:
                        local_old += value2
                        new_entity += value2
                    else:
                        local_new += value2
                        ent_id = str(key2)
                    total += value2
                if local_new < local_old:
                    ent_id = '0'
                entity_storage[key][1] = local_new
                entity_storage[key][2] = local_old
                entity_storage[key][3] = ent_id
                if current_row >= table.rowCount():
                    table.insertRow(current_row)
                x = QTableWidgetItem(ent_id)
                x.setTextAlignment(Qt.AlignCenter)
                table.setItem(entity_storage[key][0], 1,
                              x)
                y = QTableWidgetItem(os.path.basename(key))
                y.setTextAlignment(Qt.AlignCenter)
                table.setItem(entity_storage[key][0], 0, y)
                table.setHidden(True)
                table.setHidden(False)
                new_window.setFocus()
                ui_window.pics_count.setText(
                    "Количество обработанных картинок: " + str(total))
                ui_window.new_count.setText(
                    "Количество изображений новых особей: " + str(new_entity))

            if th1.is_alive():
                continue
            if last_pass:
                break
            last_pass = True
        ui_window.status.setText("Статус выполнения: завершено!")
        f = open('../results.csv',mode="w+",encoding='utf8')
        f.write("folder;ID\n")
        for i in range(table.rowCount()):
            f.write(f"{table.item(i,0).text()};{table.item(i,1).text()}\n")
        f.close()

    if mode == '1':
        th = threading.Thread(target=local_func_one_folder,
                              daemon=True)
        th.start()
        th.join(0.01)
    else:
        th = threading.Thread(target=local_func_recur,
                              daemon=True)
        th.start()
        th.join(0.01)


def uploadController(main_window: QMainWindow, new_window: QMainWindow,
                     ui_window) -> Callable:
    def upload():
        path = str(
            QFileDialog.getExistingDirectory(
                main_window, 'Выберите папку: ', '')
        )
        if not path:
            return
        main_window.setHidden(True)
        main_function(path, new_window, ui_window)

    return upload


def uploadControllerSecond(new_window: QMainWindow,
                           ui_window) -> Callable:
    def upload(path):
        main_function(path, new_window, ui_window)

    return upload
