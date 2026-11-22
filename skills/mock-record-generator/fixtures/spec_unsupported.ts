// Fixture: one supported field and two unsupported lines, for the exit 1 path.
interface Order {
  orderId: string;
  tags: string[];
  shipping: {
    city: string;
  };
}
