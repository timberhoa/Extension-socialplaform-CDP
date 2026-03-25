# Tài khoản bị logout khỏi google

**Đặc điểm nhận diện:**

* Tắt profile mở lại là logout Google (chỉ một số máy gặp tình trạng này)

**Nguyên nhân:**

* Tại một số máy chưa rõ tại sao tùy chọn đồng bộ dữ liệu lên Google được bật mặc định
* Các trình duyệt tự build không sử dụng API key của Google để đồng bộ dữ liệu nên nếu tùy chọn đồng bộ được bật thì khi mở lại cookie Google không được chấp nhận nên bị logout

**Cách xử lý:**

Thêm file "fixed\_params.txt" ở thư mục cài đặt GPMLogin rồi nhập vào nội dung "--disable-sync". Nếu file đã có sẵn, chỉ cần chỉnh sửa theo nội dung trên

<figure><img src="https://lh7-us.googleusercontent.com/fFW2V5bRP-0xl2l4-34GdiP0WSUHwXKsZ3WohC3XnizjTRIXeNTOC48TLKoG2t-w_RXaxfaVG17LtCYxT3kse-Tm7tzRY2KxgWmSX--u2bwySRM2BArMgYv81kgzJB4ACGOC1hlVPpiWAafByc7KC6Y" alt=""><figcaption></figcaption></figure>

<br>
