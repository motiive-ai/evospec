package com.acme.orders;

import javax.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(name = "customer_id", nullable = false)
    private String customerId;

    @Column(nullable = false)
    private String status; // draft, pending_payment, confirmed, shipped, delivered, cancelled

    @Column(name = "total_amount", nullable = false)
    private BigDecimal totalAmount;

    @Column(name = "currency", nullable = false)
    private String currency;

    @Column(name = "payment_id")
    private String paymentId;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at")
    private Instant updatedAt;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<LineItem> lineItems;

    // Getters and setters omitted for brevity
}
