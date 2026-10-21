"""Hàng đợi chấm bài chạy nền (một luồng), để trang web không phải chờ chấm xong.

Chỉ lần nộp mới nhất của mỗi đội được chấm; lần cũ còn trong hàng đợi thì bỏ qua.
"""
import os
import queue
import threading
import traceback

import kho
from cham import cham_doi, nap_phieu, tim_phieu
from doc_phieu_word import LoiDocPhieu

_hang_doi = queue.Queue()
_dang_cho = set()
_khoa = threading.Lock()


def dua_vao(lan_nop_id):
    with _khoa:
        if lan_nop_id in _dang_cho:
            return
        _dang_cho.add(lan_nop_id)
    kho.dat_ket_qua(lan_nop_id, "cho_cham")
    _hang_doi.put(lan_nop_id)


def cham_ngay(lan_nop_id):
    lan_nop = kho.lay_lan_nop(lan_nop_id)
    kho.dat_ket_qua(lan_nop_id, "dang_cham")
    duong_dan_phieu = tim_phieu(lan_nop["thu_muc"])
    phieu, phieu_canh_bao = None, []
    if duong_dan_phieu:
        try:
            phieu, phieu_canh_bao = nap_phieu(duong_dan_phieu)
        except LoiDocPhieu as e:
            phieu_canh_bao = [str(e)]
    bao_cao = cham_doi(lan_nop["thu_muc"], lan_nop["ma_doi"], phieu, phieu_canh_bao)
    bao_cao["phieu_nguon"] = os.path.basename(duong_dan_phieu) if duong_dan_phieu else None
    kho.dat_ket_qua(lan_nop_id, "da_cham", bao_cao=bao_cao, phieu=phieu or {})


def _lam_viec():
    while True:
        lan_nop_id = _hang_doi.get()
        with _khoa:
            _dang_cho.discard(lan_nop_id)
        try:
            lan_nop = kho.lay_lan_nop(lan_nop_id)
            if lan_nop["loi_nop"]:  # lần nộp lỗi không bao giờ được chấm
                continue
            moi_nhat = kho.lan_nop_moi_nhat(lan_nop["ma_doi"])
            if moi_nhat and moi_nhat["id"] != lan_nop_id:
                kho.dat_ket_qua(lan_nop_id, "bo_qua", loi="Đã có lần nộp mới hơn")
                continue
            cham_ngay(lan_nop_id)
        except Exception:
            kho.dat_ket_qua(lan_nop_id, "loi", loi=traceback.format_exc())


def khoi_dong():
    threading.Thread(target=_lam_viec, daemon=True, name="cham-bai").start()
    for lan_nop_id in kho.ds_chua_xong():  # bị dừng giữa chừng ở lần chạy trước
        dua_vao(lan_nop_id)
