# converz-ai-shop

## Design Choices

### Layers

The application is split into three layers:

**Route layer** receives the HTTP request, validates input, delegates to the service layer, and returns the response. It knows nothing about the database.

**Service layer** holds business logic: orchestrating operations, enforcing rules, and coordinating between multiple repositories when needed. It knows what needs to happen but not how data is stored.

**Repository layer** owns all database access. Each repository speaks directly to the ORM and exposes a clean interface (e.g. `get_by_id`, `list`, `save`). The service layer never writes a query directly.

This keeps HTTP concerns, business logic, and persistence concerns separate and independently testable.

### Database sessions and atomicity

Flask-SQLAlchemy gives you one session per request. Repositories only add objects to the session and flush when they need a generated ID. The service layer is the one that calls commit, once, after all the work is done. This means either everything lands in the database together or nothing does.

If something goes wrong the service rolls back the session. The request teardown cleans up the session regardless, but it does not roll back on its own, so the service has to be explicit about it.

### Tables

**products**
The core table. Stores everything about a product including price, stock, availability, dimensions, and metadata.

**categories**
A managed list of categories (e.g. "Beauty", "Electronics"). Has its own table because categories are real entities with a name, slug, and creation date. The app has a dedicated endpoint to list all categories.

**product_categories**
Links products to categories. A product can belong to many categories and a category can have many products.

**reviews**
Stores customer reviews for a product. Each review has a rating, comment, and reviewer details. Reviews accumulate over time and are always tied to a specific product.

**outbox**
Keeps track of changes that need to be synced to Elasticsearch. When a product is created or updated, a row is written here in the same database transaction. A background worker reads this table and pushes the changes to Elasticsearch. This ensures the search index never permanently drifts from the database.


### Why not CDC

Change Data Capture with Debezium and Kafka is the cleaner solution at scale. Debezium tails the MySQL binlog and publishes every change as an event to Kafka. A consumer picks it up and updates Elasticsearch. The application never has to think about syncing at all, and you can bolt on more consumers later without touching a line of app code.

The reason we are not doing it here is that it would mean running Kafka, Zookeeper, and Debezium just to keep one search index in sync for a small shop API. The outbox gets the job done with a single table and a background worker, which is the right amount of complexity for the problem we actually have.

### Outbox pattern

The naive approach to keeping Elasticsearch in sync is to write to the database and then call Elasticsearch in the same request. The problem is that if the Elasticsearch call fails, you have no record that it failed and the search index silently falls behind.

The outbox table solves this. When a product is created or updated, an outbox row is written in the same database transaction as the product change. A background worker then reads pending rows, pushes them to Elasticsearch, and marks them as sent. Because the outbox row is committed together with the product change, there is no window where a change can be lost. If the worker fails, the row stays pending and gets retried. The search index will always catch up eventually.

### Why some things are not separate tables

**Tags** are stored as a JSON array on the product (e.g. `["mascara", "foundation"]`). They have no metadata, there is no API to manage them, and all tag-based filtering goes through Elasticsearch. A separate tags table would add complexity with no real benefit.

**Images** are stored as a JSON array on the product (e.g. `[{"url": "...", "sort_order": 0}]`). Images are always fetched as part of a product and there is no API to manage them individually.

**Brands** are stored as a plain text column on the product. There is no brand management API and brands carry no metadata beyond their name, so a separate table would be unnecessary.

A separate product summary table was also considered but dropped. Elasticsearch already stores a denormalized version of each product for fast listing and search, so maintaining a second copy in MySQL would mean keeping three things in sync on every write.
