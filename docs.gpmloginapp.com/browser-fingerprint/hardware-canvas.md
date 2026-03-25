# Hardware: Canvas

Canvas là một HTML5 API, nó được sử dụng để vẽ (render) 2D để hiển thị lên Browser, ví dụ như một hình tròn, hình tam giác, render một đoạn chữ thành hình ảnh và nhiều thứ khác. Các hình 2D này hơi khác nhau ở các loại card màn hình (mắt thường khó có thể thể phân biệt) nên đây có thể sử dụng là một trong các thông số xác định sự khác nhau giữa các loại card màn hình.

Antidetect browser sử dụng <mark style="color:blue;">kĩ thuật noise</mark> (làm nhiễu) để hình ảnh sau khi render có hơi khác một chút so với render gốc.

**Đặc điểm của kĩ thuật noise**

1 . Kĩ thuật noise không thể biến hình ảnh sau render của card đồ họa A giống hệt với hình ảnh sau render của card đồ họa B, giống như việc phẫu thuật thẩm mỹ, không thể phẫu thuật người A thành người B được (tất cả chi tiết từng chân tơ kẽ tóc), mà chỉ làm người A lúc sau khác với người A lúc trước.&#x20;

2 . Kĩ thuật này giúp tạo nên sự đa dạng và tính duy nhất rất lớn cho fingerprint.

3 . Kĩ thuật noise có thể bị phát hiện bởi các hệ thống lớn có thu thập big data để kiểm tra

Nếu chỉ xét riêng một thông số canvas, có hàng chục triệu máy tính khác nhau trên khắp thế giới giống nhau (sử dụng cùng loại card đồ họa, cài cùng hệ điều hành và trình duyệt), nhưng kĩ thuật noise sẽ khiến bạn có tính duy nhất rất cao.

Ví dụ đơn giản:&#x20;

Facebook có hàng tỉ người truy cập mỗi ngày, họ thu thập các mã hash canvas lưu lại, khi bạn truy cập nếu bạn giống rất nhiều người khác là điều bình thường, nhưng bạn là duy nhất mới là điều đáng nghi và gần như không thể xảy ra (bạn không thể sử dụng một loại card đồ họa, cài hệ điều hành và trình duyệt mà không ai trong số hàng tỉ người đó có)
