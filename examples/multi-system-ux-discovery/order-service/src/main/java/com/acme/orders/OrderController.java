package com.acme.orders;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @PostMapping("/")
    public ResponseEntity<Order> createOrder(@RequestBody CreateOrderRequest request) {
        return ResponseEntity.ok(orderService.create(request));
    }

    @GetMapping("/{orderId}")
    public ResponseEntity<Order> getOrder(@PathVariable String orderId) {
        return ResponseEntity.ok(orderService.findById(orderId));
    }

    @PostMapping("/{orderId}/items")
    public ResponseEntity<Order> addLineItem(
            @PathVariable String orderId,
            @RequestBody AddLineItemRequest request) {
        return ResponseEntity.ok(orderService.addItem(orderId, request));
    }

    @DeleteMapping("/{orderId}/items/{itemId}")
    public ResponseEntity<Order> removeLineItem(
            @PathVariable String orderId,
            @PathVariable String itemId) {
        return ResponseEntity.ok(orderService.removeItem(orderId, itemId));
    }

    @PostMapping("/{orderId}/checkout")
    public ResponseEntity<Order> checkout(@PathVariable String orderId) {
        return ResponseEntity.ok(orderService.checkout(orderId));
    }

    @PostMapping("/{orderId}/cancel")
    public ResponseEntity<Order> cancelOrder(@PathVariable String orderId) {
        return ResponseEntity.ok(orderService.cancel(orderId));
    }

    @GetMapping("/customer/{customerId}")
    public ResponseEntity<?> getCustomerOrders(@PathVariable String customerId) {
        return ResponseEntity.ok(orderService.findByCustomer(customerId));
    }

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }
}
