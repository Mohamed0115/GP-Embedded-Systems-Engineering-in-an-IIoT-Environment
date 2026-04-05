# IIoT PostgreSQL Database Architecture

Below is the recommended Entity-Relationship (ER) schema designed for your IIoT platform. It supports Role-Based Access Control (RBAC), machine image annotations, gateway channel mapping, and high-frequency time-series data.

## Entity-Relationship Diagram

```mermaid
erDiagram
    Users ||--o{ User_Roles : has
    Roles ||--o{ User_Roles : assigned_to

    Users ||--o{ Machines : manages
    
    Machines ||--o{ Sensors : contains
    Gateways ||--o{ Sensors : connects_to

    Sensors ||--o{ Sensor_Readings : generates

    Users {
        uuid id PK
        string username
        string password_hash
        string email
        timestamp created_at
    }

    Roles {
        int id PK
        string role_name "e.g., Admin, Manager, Engineer"
        jsonb permissions
    }

    User_Roles {
        uuid user_id FK
        int role_id FK
    }

    Gateways {
        uuid id PK
        string name "e.g., ITA-Main, CTC-Zone1"
        string type "ITA-110, CTC Connect"
        string ip_address
        int port
        boolean is_active
    }

    Machines {
        uuid id PK
        uuid owner_id FK "User who created it"
        string name "e.g., Motor A"
        string image_url "Path to blueprint uploaded"
        string location
        timestamp created_at
    }

    Sensors {
        uuid id PK
        uuid machine_id FK
        uuid gateway_id FK
        string name "e.g., Bearing Temp 1"
        string sensor_type "Vibration, Temperature"
        
        %% Image Mapping
        float image_pos_x "X coordinate for clickable map"
        float image_pos_y "Y coordinate for clickable map"
        
        %% Gateway Mapping
        int gateway_channel_x "ITA X Channel"
        int gateway_channel_y "ITA Y Channel"
        int gateway_channel_z "ITA Z Channel"
    }

    Sensor_Readings {
        timestamp time PK "TimescaleDB Time Column"
        uuid sensor_id PK, FK
        float rms_x
        float rms_y
        float rms_z
        jsonb raw_data_payload "Actual arrays of FFT/Time data (Optional depending on storage size)"
    }
```

## Core Architectural Pillars

### 1. User Authentication & RBAC (Role-Based Access Control)
Instead of hardcoding users, we separate auth into `Users` and `Roles`.
*   **Users Table**: Never store plain passwords; always use hashes (e.g., `bcrypt`).
*   **Roles Table**: Defines what a user can do. See the main chat response for role definitions.

### 2. Physical Asset Mapping (Machines & Images)
*   **Machines Table**: Stores the machine's name and an `image_url` (path to where the image is stored on your server/bucket).
*   **Sensors Table**: Holds `image_pos_x` and `image_pos_y` to overlay a clickable dot right onto the machine's blueprint on the frontend.

### 3. Gateway & Channel Mapping
*   **Gateways Table**: Stores connection parameters centrally.
*   **Sensors Table**: Since the ITA gateway has multiple channels (up to 16 for X/Y/Z), the `Sensors` table stores exactly which channel mapping this particular sensor relies on.

### 4. TimescaleDB (Time-Series Data)
*   The `Sensor_Readings` table should be configured as a **TimescaleDB Hypertable**.
*   Instead of storing raw 32,000-point arrays for *every* reading (which will explode your database size), calculate metrics (RMS, Peak, Crest Factor) and store those as floats. If you must store the raw array charts, compress them as binary or JSONB, or store them in cheap object storage (AWS S3 / local files) and put the "FilePath" in this database.
