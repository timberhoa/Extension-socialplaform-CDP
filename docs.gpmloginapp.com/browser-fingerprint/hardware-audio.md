# Hardware: Audio

Tương tự với Canvas, WebGL là đặc trưng của các loại card đồ họa, thì Audio context là đặc trưng của card âm thanh.

Việc xử lý cũng tương tự là sử dụng <mark style="color:blue;">kĩ thuật noise</mark> để âm thanh sau khi render khác với âm thanh gốc, từ đó tạo sự khác nhau về fingerprint.

**Đặc điểm của kĩ thuật noise**

1 . Kĩ thuật noise không thể biến hình ảnh sau render của card đồ họa A giống hệt với hình ảnh sau render của card đồ họa B, giống như việc phẫu thuật thẩm mỹ, không thể phẫu thuật người A thành người B được (tất cả chi tiết từng chân tơ kẽ tóc), mà chỉ làm người A lúc sau khác với người A lúc trước.&#x20;

2 . Kĩ thuật này giúp tạo nên sự đa dạng và tính duy nhất rất lớn cho fingerprint.

3 . Kĩ thuật noise có thể bị phát hiện bởi các hệ thống lớn có thu thập big data để kiểm tra

Nếu chỉ xét riêng một thông số canvas, có hàng chục triệu máy tính khác nhau trên khắp thế giới giống nhau (sử dụng cùng loại card đồ họa, cài cùng hệ điều hành và trình duyệt), nhưng kĩ thuật noise sẽ khiến bạn có tính duy nhất rất cao.

Ví dụ đơn giản:&#x20;

Facebook có hàng tỉ người truy cập mỗi ngày, họ thu thập các mã hash canvas lưu lại, khi bạn truy cập nếu bạn giống rất nhiều người khác là điều bình thường, nhưng bạn là duy nhất mới là điều đáng nghi và gần như không thể xảy ra (bạn không thể sử dụng một loại card đồ họa, cài hệ điều hành và trình duyệt mà không ai trong số hàng tỉ người đó có)
