"""Gọi Google Drive API v3 bằng tài khoản Google cá nhân (OAuth refresh token).

Biến môi trường: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN (lấy bằng lay_token_drive.py).
Quyền drive.file: chỉ thấy/sửa file do chính ứng dụng tạo ra, không đụng file khác trong Drive.
"""
import json
import os
import random
import threading
import time
import uuid

import httpx

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/drive/v3/files"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
THU_MUC = "application/vnd.google-apps.folder"
TRUONG = "id,name,mimeType,appProperties,createdTime"


class LoiDrive(Exception):
    pass


def _q(chuoi):
    return chuoi.replace("\\", "\\\\").replace("'", "\\'")


class DriveApi:
    def __init__(self):
        try:
            self._client_id = os.environ["GOOGLE_CLIENT_ID"]
            self._client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
            self._refresh = os.environ["GOOGLE_REFRESH_TOKEN"]
        except KeyError as e:
            raise LoiDrive("Thiếu biến môi trường %s" % e)
        self._token, self._het_han = None, 0
        self._khoa = threading.Lock()
        self._http = httpx.Client(timeout=60)

    def _lay_token(self, ep=False):
        with self._khoa:
            if ep or not self._token or time.time() > self._het_han - 60:
                r = self._http.post(TOKEN_URL, data={"client_id": self._client_id, "client_secret": self._client_secret,
                                                     "refresh_token": self._refresh, "grant_type": "refresh_token"})
                if r.status_code != 200:
                    raise LoiDrive("Không lấy được quyền truy cập Google Drive: %s" % r.text[:300])
                du_lieu = r.json()
                self._token, self._het_han = du_lieu["access_token"], time.time() + du_lieu.get("expires_in", 3600)
            return self._token

    def _goi(self, method, url, headers=None, **kw):
        for lan in range(6):
            h = dict(headers or {})
            h["Authorization"] = "Bearer " + self._lay_token(ep=lan > 0 and r.status_code == 401)
            r = self._http.request(method, url, headers=h, **kw)
            if r.status_code in (401, 429, 500, 502, 503, 504) and lan < 5:
                if r.status_code != 401:
                    time.sleep(min(2 ** lan, 16) + random.random())  # Drive giới hạn tốc độ: chờ rồi thử lại
                continue
            if r.status_code >= 400:
                raise LoiDrive("Google Drive báo lỗi %d: %s" % (r.status_code, r.text[:300]))
            return r
        raise LoiDrive("Google Drive không phản hồi")

    def _tim(self, q):
        ket_qua, trang = [], None
        while True:
            params = {"q": q + " and trashed = false", "fields": "nextPageToken,files(%s)" % TRUONG,
                      "pageSize": 1000, "spaces": "drive"}
            if trang:
                params["pageToken"] = trang
            du_lieu = self._goi("GET", API, params=params).json()
            ket_qua += du_lieu.get("files", [])
            trang = du_lieu.get("nextPageToken")
            if not trang:
                return ket_qua

    # ---- giao diện dùng chung với bản giả lập để test ----

    def con(self, cha, chi_thu_muc=False):
        q = "'%s' in parents" % _q(cha)
        if chi_thu_muc:
            q += " and mimeType = '%s'" % THU_MUC
        return self._tim(q)

    def tim_theo_nhan(self, nhan):
        return self._tim(" and ".join("appProperties has { key='%s' and value='%s' }" % (_q(k), _q(v))
                                      for k, v in nhan.items()))

    def tao_thu_muc(self, ten, cha, nhan):
        meta = {"name": ten, "mimeType": THU_MUC, "appProperties": nhan}
        if cha:
            meta["parents"] = [cha]
        return self._goi("POST", API, params={"fields": "id"}, json=meta).json()["id"]

    def tai_len(self, ten, cha, noi_dung, mime, nhan=None):
        meta = {"name": ten, "parents": [cha]}
        if nhan:
            meta["appProperties"] = nhan
        ranh_gioi = uuid.uuid4().hex
        than = ("--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n%s\r\n--%s\r\nContent-Type: %s\r\n\r\n"
                % (ranh_gioi, json.dumps(meta), ranh_gioi, mime)).encode() + noi_dung + ("\r\n--%s--" % ranh_gioi).encode()
        r = self._goi("POST", UPLOAD, params={"uploadType": "multipart", "fields": "id"}, content=than,
                      headers={"Content-Type": "multipart/related; boundary=%s" % ranh_gioi})
        return r.json()["id"]

    def ghi_de(self, file_id, noi_dung, mime):
        self._goi("PATCH", "%s/%s" % (UPLOAD, file_id), params={"uploadType": "media"}, content=noi_dung,
                  headers={"Content-Type": mime})

    def sua_nhan(self, file_id, nhan):
        self._goi("PATCH", "%s/%s" % (API, file_id), params={"fields": "id"}, json={"appProperties": nhan})

    def tai_ve(self, file_id):
        return self._goi("GET", "%s/%s" % (API, file_id), params={"alt": "media"}).content
