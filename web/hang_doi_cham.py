"""Chấm bài.

- Trên máy cá nhân / VPS: hàng đợi chấm nền (một luồng), trang web không phải chờ.
- Trên Vercel (serverless, không chạy nền được): chấm ngay trong request admin bấm - "đồng bộ".
Chỉ lần nộp mới nhất của mỗi đội được chấm; lần cũ còn trong hàng đợi thì bỏ qua.
"""
import os
import queue
import threading
import traceback

import kho
from cham import cham_doi, nap_phieu, tim_phieu
from doc_phieu_word import LoiDocPhieu
from kiem_tra_nop import kiem_tra

DONG_BO = bool(os.environ.get("VERCEL")) or os.environ.get("CHE_DO_CHAM") == "dong_bo"

_hang_doi = queue.Queue()
_dang_cho = set()
_khoa = threading.Lock()


def dua_vao(lan_nop_id):
    if DONG_BO:
        cham_ngay(lan_nop_id)
        return
    with _khoa:
        if lan_nop_id in _dang_cho:
            return
        _dang_cho.add(lan_nop_id)
    kho.dat_ket_qua(lan_nop_id, "cho_cham")
    _hang_doi.put(lan_nop_id)


def cham_ngay(lan_nop_id):
    try:
        lan_nop = kho.lay_lan_nop(lan_nop_id)
        kho.dat_ket_qua(lan_nop_id, "dang_cham")
        thu_muc = kho.thu_muc_lam_viec(lan_nop)
        if not lan_nop.get("kiem_tra"):  # nộp qua Apps Script: kiểm tra định dạng lúc chấm để admin xem
            kho.luu_kiem_tra(lan_nop_id, kiem_tra(thu_muc)[0])
        duong_dan_phieu = tim_phieu(thu_muc)
        phieu, phieu_canh_bao = None, []
        if duong_dan_phieu:
            try:
                phieu, phieu_canh_bao = nap_phieu(duong_dan_phieu)
            except LoiDocPhieu as e:
                phieu_canh_bao = [str(e)]
        bao_cao = cham_doi(thu_muc, lan_nop["ma_doi"], phieu, phieu_canh_bao)
        bao_cao["phieu_nguon"] = os.path.basename(duong_dan_phieu) if duong_dan_phieu else None
        kho.dat_ket_qua(lan_nop_id, "da_cham", bao_cao=bao_cao, phieu=phieu or {})
    except Exception:
        kho.dat_ket_qua(lan_nop_id, "loi", loi=traceback.format_exc())


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
        except Exception:
            kho.dat_ket_qua(lan_nop_id, "loi", loi=traceback.format_exc())
            continue
        cham_ngay(lan_nop_id)


def khoi_dong():
    if DONG_BO:
        return
    threading.Thread(target=_lam_viec, daemon=True, name="cham-bai").start()
    for lan_nop_id in kho.ds_chua_xong():  # bị dừng giữa chừng ở lần chạy trước
        dua_vao(lan_nop_id)
