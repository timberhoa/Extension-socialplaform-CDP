# Báo đỏ ở một số trang check

Các trang check fingerprint có đánh giá xanh / đỏ chỉ mang tính chất tương đối, tuy nhiên chúng check khá chính xác về mặt kỹ thuật, vì vậy cũng có thể dựa vào chúng để đánh giá một phần chất lượng fingerprint.

Ở thời điểm hiện tại, rất nhiều hệ thống lớn đã bắt đầu để ý tới các dạng antidetect browser, họ thu thập toàn bộ fingerprint của thiết bị thật có trên thị trường để đánh giá fingerprint thông qua database của họ, vì vậy có thể về phương pháp kỹ thuật, fingerprint vẫn có thể vượt qua các bài kiểm duyệt, tuy nhiên có thể bị phát hiện thông qua việc sử dụng database, chính vì vậy khi dùng antidetect browser với các hệ thống lớn, các phần mềm lớn hiện tại đều khuyên người dùng tắt kĩ thuật NOISE.\
\
**Đỏ mục IP**

Bạn bị phát hiện đang sử dụng proxy, hãy thay thế proxy hiện tại

**Đỏ Location**

Thông thường là trường hợp lệch timezone của website với bên API xác định timezone từ IP, ví dụ ở VN, timezone có thể trả ra là Asia/Ho\_Chi\_Minh, hoặc Asia/Bankok (miễn là múi giờ +7), các hệ thống phiên từ IP sang Timezone có thể lệch nhau nhưng nhìn chung là không ảnh hưởng quá nhiều.

**Đỏ hardware**

Fingerprint đã bị phát hiện đang sai về thông số kĩ thuật so với thiết bị thật, nhưng đôi khi cũng do website check chưa cập nhật kĩ thuật check cho phiên bản trình duyệt mới nhất.

**Đỏ software (hoặc browser)**

Thường là do Useragent từ request  không khớp với Useragent trả ra từ Javascript. (xảy ra khi người dùng tự dùng các extension đổi user agent mà không thông qua chức năng trên antidetect)
