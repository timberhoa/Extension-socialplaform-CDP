# Programming

**Chức năng các action**

Chi tiết sử dụng từng action xem bên dưới.

<table data-full-width="false"><thead><tr><th width="269">Action</th><th>Mô tả</th></tr></thead><tbody><tr><td>Declare variable</td><td>Khai báo một biến</td></tr><tr><td>Random number</td><td>Tạo một số ngẫu nhiên</td></tr><tr><td>Split text</td><td>Cắt chuỗi thành một mảng kí tự</td></tr><tr><td>Math execute</td><td>Thực hiện một chuỗi phép toán</td></tr><tr><td>Read random line</td><td>Đọc dòng ngẫu nhiên ở một file txt</td></tr><tr><td>Delay</td><td>Dừng chờ</td></tr><tr><td>Http Get</td><td>Thực hiện request GET</td></tr><tr><td>Http Post</td><td>Thực hiện request POST</td></tr><tr><td>Http Download</td><td>Thực hiện request DOWNLOAD</td></tr><tr><td>Read Json</td><td>Đọc một node của json</td></tr><tr><td>Break loop</td><td>Thoát vòng lặp</td></tr><tr><td>Create excel workbook</td><td>Tạo file excel</td></tr><tr><td>Export excel</td><td>Ghi excel</td></tr><tr><td>Get clipboard</td><td>Lấy đoạn text đang lưu trong bộ nhớ</td></tr><tr><td>Set clipboard</td><td>Set text vào trong bộ nhớ</td></tr></tbody></table>

<mark style="color:red;">**Chú ý: tất cả các đầu vào đều có thể nhúng các biến khác bằng định dạng $TÊN\_BIẾN**</mark>

**Video chi tiết từng chức năng:**

<https://youtu.be/mfLT9FnHq4E>

### Giải thích thêm một số chức năng phức tạp

**Read Json**

* Đầu vào: định dạng Json;node 1;node 2;node 3....

```
Ví dụ có một json như sau được lưu vào biến $ketQua

{
    "name": "Test profile",
    "info": {
        "created_at": "2023-11-11",
        "author": "buiducduygame"
    }
}

Để đọc được author dùng như sau:
$ketQua;info;author
```

* Đầu ra: tên biến lưu kết quả
