# Trip Itinerary Generation - Flowchart

## Tổng quan quy trình tạo lịch trình du lịch

```mermaid
flowchart TD
    subgraph Input["INPUT - Yêu cầu từ người dùng"]
        A[User Request] --> A1[City: Thành phố]
        A --> A2[Start Date: Ngày bắt đầu]
        A --> A3[Num Days: Số ngày]
        A --> A4[Num People: Số người]
        A --> A5[Preferred Tags: Sở thích]
        A --> A6[Block Time Config: Cấu hình thời gian]
    end

    subgraph API["API LAYER"]
        B[POST /trip] --> C[ItineraryRequest Validation]
        C --> D{Valid Request?}
        D -->|No| E[Return Error 400]
        D -->|Yes| F[Call Trip Service]
    end

    subgraph Service["SERVICE LAYER"]
        F --> G[get_trip_itinerary]
        G --> H[Fetch Places by City]
        G --> I[Fetch Food Places by City]
        H --> J[Convert to ItinerarySpot]
        I --> J
    end

    subgraph Engine["ITINERARY ENGINE"]
        J --> K[build_trip_itinerary]
        K --> L[Initialize AI Recommender]
        L --> M[Preload AI Scores]
        
        M --> N{For Each Day}
        N --> O[Create TripContext]
        O --> P[Filter Unused Spots]
        P --> Q[build_day_itinerary]
    end

    subgraph DayBuilder["BUILD DAY ITINERARY"]
        Q --> R{Morning Enabled?}
        R -->|Yes| S[build_visit_block - Morning]
        R -->|No| T[Skip Morning]
        
        S --> U{Lunch Enabled?}
        T --> U
        U -->|Yes| V[pick_meal_block - Lunch]
        U -->|No| W[Skip Lunch]
        
        V --> X{Afternoon Enabled?}
        W --> X
        X -->|Yes| Y[build_visit_block - Afternoon]
        X -->|No| Z[Skip Afternoon]
        
        Y --> AA{Dinner Enabled?}
        Z --> AA
        AA -->|Yes| AB[pick_meal_block - Dinner]
        AA -->|No| AC[Skip Dinner]
        
        AB --> AD{Evening Enabled?}
        AC --> AD
        AD -->|Yes| AE[build_visit_block - Evening]
        AD -->|No| AF[Skip Evening]
    end

    subgraph BlockBuilder["BUILD VISIT BLOCK"]
        BV[build_visit_block] --> BV1[Get Available Spots]
        BV1 --> BV2[sort_spots_diverse - AI + Rules]
        BV2 --> BV3{While Time Available}
        BV3 -->|Yes| BV4[Calculate Candidates Score]
        BV4 --> BV5[Random Select from Top 5]
        BV5 --> BV6[Add to Block Items]
        BV6 --> BV7[Update Current Time]
        BV7 --> BV3
        BV3 -->|No| BV8[Spread Extra Time]
        BV8 --> BV9[Return Block Items]
    end

    subgraph Scoring["SPOT SCORING"]
        SC1[calculate_spot_weight] --> SC2[AI Score - 40%]
        SC1 --> SC3[Tag Match Score]
        SC1 --> SC4[Distance Score]
        SC1 --> SC5[Must Visit Bonus]
        SC1 --> SC6[Diversity Penalty]
        SC1 --> SC7[Random Factor ±30%]
        SC2 --> SC8[Final Score]
        SC3 --> SC8
        SC4 --> SC8
        SC5 --> SC8
        SC6 --> SC8
        SC7 --> SC8
    end

    subgraph Output["OUTPUT"]
        AE --> AG[Calculate Day Cost]
        AF --> AG
        AG --> AH[Create DayItineraryResponse]
        AH --> AI{More Days?}
        AI -->|Yes| N
        AI -->|No| AJ[Compile Trip Response]
        AJ --> AK[Save to History if user_id]
        AK --> AL[Return JSON Response]
    end

    Input --> API
    Engine --> DayBuilder
    DayBuilder --> BlockBuilder
    BlockBuilder --> Scoring
    DayBuilder --> Output

    style Input fill:#e1f5fe
    style API fill:#fff3e0
    style Service fill:#f3e5f5
    style Engine fill:#e8f5e9
    style DayBuilder fill:#fce4ec
    style BlockBuilder fill:#fff8e1
    style Scoring fill:#f1f8e9
    style Output fill:#e0f2f1
```

---

## Chi tiết các bước chính

### Nhận Request từ Frontend
```
ItineraryRequest {
    city: "Hồ Chí Minh"
    start_date: "2025-12-20"
    num_days: 3
    num_people: 2
    preferred_tags: ["history", "food", "culture"]
    morning: {enabled: true, start: "08:00", end: "11:30"}
    lunch: {enabled: true, start: "11:30", end: "13:00"}
    afternoon: {enabled: true, start: "13:30", end: "17:30"}
    dinner: {enabled: true, start: "18:00", end: "19:30"}
    evening: {enabled: true, start: "20:00", end: "22:00"}
}
```

### Lấy dữ liệu địa điểm
- **Places**: Địa điểm tham quan (museum, park, landmark...)
- **Food Places**: Quán ăn, nhà hàng
- Convert sang `ItinerarySpot` với thông tin: lat/lng, giờ mở cửa, rating, tags...

### AI-Powered Scoring
```
Score = (AI_Score × 0.3) + Tag_Match + Distance_Bonus - Diversity_Penalty + Random_Factor
```

### Build từng Block trong ngày
- **Morning**: 2-3 địa điểm tham quan
- **Lunch**: 1 quán ăn gần vị trí cuối morning
- **Afternoon**: 2-3 địa điểm tham quan  
- **Dinner**: 1 quán ăn gần vị trí cuối afternoon
- **Evening**: 1 địa điểm giải trí/cafe

### Output Response
```json
{
    "city": "Hồ Chí Minh",
    "start_date": "2025-12-20",
    "num_days": 3,
    "days": [
        {
            "date": "2025-12-20",
            "blocks": {
                "morning": [...],
                "lunch": [...],
                "afternoon": [...],
                "dinner": [...],
                "evening": [...]
            },
            "cost_summary": {
                "total_attraction_cost_vnd": 150000,
                "total_food_cost_vnd": 300000
            }
        }
    ]
}
```

---

## Sequence Diagram - Tương tác giữa các thành phần

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as Trip Router
    participant SVC as Trip Service
    participant REPO as Repositories
    participant ENG as Itinerary Engine
    participant AI as AI Recommender
    participant DB as Database

    FE->>API: POST /trip (ItineraryRequest)
    API->>SVC: get_trip_itinerary(req)
    
    SVC->>REPO: fetch_place_lites_by_city(city)
    REPO->>DB: SELECT * FROM places
    DB-->>REPO: Places data
    REPO-->>SVC: PlaceLite[]
    
    SVC->>REPO: fetch_food_places_by_city(city)
    REPO->>DB: SELECT * FROM food_places
    DB-->>REPO: Food data
    REPO-->>SVC: FoodPlace[]
    
    SVC->>ENG: build_trip_itinerary(req, spots, foods)
    
    ENG->>AI: preload_ai_scores(spots, tags)
    AI-->>ENG: AI scores loaded
    
    loop For each day
        ENG->>ENG: build_day_itinerary(context, spots, foods)
        
        loop For each block (morning, lunch, afternoon, dinner, evening)
            ENG->>AI: get_ai_score(spot_id, tags)
            AI-->>ENG: score
            ENG->>ENG: sort_spots_diverse()
            ENG->>ENG: build_visit_block() / pick_meal_block()
        end
    end
    
    ENG-->>SVC: Trip itinerary data
    SVC-->>API: Trip response
    API-->>FE: JSON Response
```

---

## Ghi chú
- **Diversity**: Hệ thống tránh chọn các địa điểm quá gần nhau hoặc cùng loại
- **Time Optimization**: Tự động điều chỉnh thời gian dwell để lấp đầy block
- **Distance Constraint**: Khoảng cách tối đa giữa 2 địa điểm liên tiếp: 5km
- **AI Integration**: Sử dụng Content-Based Filtering để đề xuất địa điểm phù hợp với sở thích
