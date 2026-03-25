# Xử lý lỗi: The network location cannot be reached

* Cách khắc phục: Mở cmd với quyền admin (cmd nha không phải powershell) và chạy lệnh: **netsh http add iplisten 127.0.0.1** hoặc **sc config http start=demand**
* Nguyên nhân: Do tool khởi tạo một HttpServer tại địa chỉ 127.0.0.1 để phục vụ việc export cookie, nhưng máy chưa cho phép lắng nghe dữ liệu tại địa chỉ này nên lỗi

<figure><img src="https://98969336-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FWmcWKgpDfbrkKf05muK8%2Fuploads%2FOJEgaFKBReOBXLaGC15O%2Fimage.png?alt=media&#x26;token=baa0ab64-51e8-4e85-9af9-b2ae5b545396" alt=""><figcaption></figcaption></figure>
