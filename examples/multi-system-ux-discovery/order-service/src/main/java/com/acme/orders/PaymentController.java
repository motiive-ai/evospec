package com.acme.orders;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;

@RestController
@RequestMapping("/api/payments")
public class PaymentController {

    @PostMapping("/authorize")
    public ResponseEntity<?> authorizePayment(@RequestBody AuthorizePaymentRequest request) {
        return ResponseEntity.ok(paymentService.authorize(request));
    }

    @PostMapping("/{paymentId}/capture")
    public ResponseEntity<?> capturePayment(@PathVariable String paymentId) {
        return ResponseEntity.ok(paymentService.capture(paymentId));
    }

    @PostMapping("/{paymentId}/refund")
    public ResponseEntity<?> refundPayment(@PathVariable String paymentId) {
        return ResponseEntity.ok(paymentService.refund(paymentId));
    }

    @GetMapping("/{paymentId}")
    public ResponseEntity<?> getPayment(@PathVariable String paymentId) {
        return ResponseEntity.ok(paymentService.findById(paymentId));
    }

    private final PaymentService paymentService;

    public PaymentController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }
}
