"""Places API routes"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from app.domain.entities.PlaceLite import PlaceLite
from app.domain.entities.Address import Address
from app.application.services.process_request import process_request  
from app.adapters.repositories.repository_factory import get_place_repository
from app.application.interfaces.place_repository import IPlaceRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/places", tags=["places"])


# ============================================================
# SCHEMAS FOR REQUEST/RESPONSE
# ============================================================

class AddressRequest(BaseModel):
    """Schema cho Address trong request"""
    houseNumber: Optional[str] = Field(None, example="01")
    street: Optional[str] = Field(None, example="Công xã Paris")
    ward: Optional[str] = Field(None, example="Phường Bến Nghé")
    district: Optional[str] = Field(None, example="Quận 1")
    city: str = Field(..., example="Thành phố Hồ Chí Minh")
    lat: Optional[float] = Field(None, ge=-90, le=90, example=10.7798)
    lng: Optional[float] = Field(None, ge=-180, le=180, example=106.6990)
    url: Optional[str] = Field(None, example="https://maps.google.com/?q=...")


class CreatePlaceRequest(BaseModel):
    """Schema cho request tạo địa điểm mới"""
    name: str = Field(..., min_length=1, max_length=255, example="Nhà Thờ Đức Bà")
    priceVnd: Optional[int] = Field(None, ge=0, example=0)
    summary: Optional[str] = Field(None, max_length=500, example="Nhà thờ kiến trúc Pháp nổi tiếng")
    description: Optional[str] = Field(None, example="Công trình kiến trúc Gothic...")
    openTime: Optional[str] = Field(None, pattern=r"^(([01]\d|2[0-3]):[0-5]\d)?$", example="06:00")
    closeTime: Optional[str] = Field(None, pattern=r"^(([01]\d|2[0-3]):[0-5]\d)?$", example="18:00")
    phone: Optional[str] = Field(None, example="028 3822 0477")
    rating: Optional[float] = Field(None, ge=0, le=5, example=4.5)
    reviewCount: Optional[int] = Field(0, ge=0, example=1234)
    popularity: Optional[int] = Field(0, ge=0, le=100, example=85)
    imageName: Optional[str] = Field(None, example="nha_tho_duc_ba.jpg")
    address: AddressRequest = Field(...)


class PlaceResponse(BaseModel):
    """Schema cho response chung"""
    success: bool
    message: str
    data: Optional[dict] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/search", response_model=dict)
async def search_places(
    province: str = Query(..., example="Hồ Chí Minh", description="Tên tỉnh/thành phố"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng kết quả tối đa"),
    repository: IPlaceRepository = Depends(get_place_repository)
):
    """
    🔍 Tìm kiếm địa điểm thông minh (3 trường hợp)
    
    - **TH1**: Database đủ → trả về luôn ⚡
    - **TH2**: Database thiếu → AI + API bổ sung 🤖
    - **TH3**: Database rỗng → AI + API tìm toàn bộ 🌐
    
    ## Query Parameters:
    - `province`: Tên tỉnh/thành phố (VD: "Hồ Chí Minh", "Đà Nẵng")
    - `limit`: Số lượng kết quả (1-100, mặc định 20)
    """
    try:
        # ✅ Gọi function process_request
        places: List[PlaceLite] = await process_request(repository, province, limit)
        
        return {
            "success": True,
            "province": province,
            "count": len(places),
            "places": [place.model_dump() for place in places]
        }
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
async def create_place(
    place_data: CreatePlaceRequest = Body(...),
    repository: IPlaceRepository = Depends(get_place_repository)
):
    """
    🆕 Tạo địa điểm mới và lưu vào database
    """
    try:
        # Convert request sang PlaceLite
        place_lite = PlaceLite(
            id=None,
            name=place_data.name,
            priceVnd=place_data.priceVnd,
            summary=place_data.summary,
            description=place_data.description,
            openTime=place_data.openTime,
            closeTime=place_data.closeTime,
            phone=place_data.phone,
            rating=place_data.rating,
            reviewCount=place_data.reviewCount or 0,
            popularity=place_data.popularity or 0,
            imageName=place_data.imageName,
            address=Address(
                houseNumber=place_data.address.houseNumber,
                street=place_data.address.street,
                ward=place_data.address.ward,
                district=place_data.address.district,
                city=place_data.address.city,
                lat=place_data.address.lat,
                lng=place_data.address.lng,
                url=place_data.address.url
            )
        )
        
        # Save to database
        place_id = await repository.save(place_lite)
        
        logger.info(f"✅ Created place '{place_data.name}' with ID: {place_id}")
        
        return PlaceResponse(
            success=True,
            message=f"Place created successfully with ID: {place_id}",
            data={
                "id": place_id,
                "name": place_data.name,
                "city": place_data.address.city
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create place: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create place: {str(e)}"
        )


@router.post("/batch", response_model=PlaceResponse)
async def create_places_batch(
    places_data: List[CreatePlaceRequest] = Body(...),
    repository: IPlaceRepository = Depends(get_place_repository)
):
    """
    📦 Tạo nhiều địa điểm cùng lúc (batch insert)
    """
    try:
        created_ids = []
        failed = []
        
        for place_data in places_data:
            try:
                place_lite = PlaceLite(
                    id=None,
                    name=place_data.name,
                    priceVnd=place_data.priceVnd,
                    summary=place_data.summary,
                    description=place_data.description,
                    openTime=place_data.openTime,
                    closeTime=place_data.closeTime,
                    phone=place_data.phone,
                    rating=place_data.rating,
                    reviewCount=place_data.reviewCount or 0,
                    popularity=place_data.popularity or 0,
                    imageName=place_data.imageName,
                    address=Address(
                        houseNumber=place_data.address.houseNumber,
                        street=place_data.address.street,
                        ward=place_data.address.ward,
                        district=place_data.address.district,
                        city=place_data.address.city,
                        lat=place_data.address.lat,
                        lng=place_data.address.lng,
                        url=place_data.address.url
                    )
                )
                
                place_id = await repository.save(place_lite)
                created_ids.append({"id": place_id, "name": place_data.name})
                
            except Exception as e:
                failed.append({"name": place_data.name, "error": str(e)})
                logger.warning(f"Failed to save '{place_data.name}': {e}")
        
        logger.info(f"✅ Batch insert: {len(created_ids)} success, {len(failed)} failed")
        
        return PlaceResponse(
            success=True,
            message=f"Created {len(created_ids)} places successfully",
            data={
                "created": created_ids,
                "failed": failed,
                "total": len(places_data)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Batch creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=dict)
async def get_all_places(
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(100, ge=1, le=1000, description="Số lượng tối đa"),
    repository: IPlaceRepository = Depends(get_place_repository)
):
    """
    📋 Lấy tất cả địa điểm từ database (có phân trang)
    """
    try:
        all_places = await repository.get_all()
        paginated_places = all_places[skip : skip + limit]
        
        return {
            "success": True,
            "total": len(all_places),
            "count": len(paginated_places),
            "skip": skip,
            "limit": limit,
            "places": [place.model_dump() for place in paginated_places]
        }
        
    except Exception as e:
        logger.error(f"❌ Get all failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{place_id}", response_model=dict)
async def get_place_by_id(
    place_id: int,
    repository: IPlaceRepository = Depends(get_place_repository)
):
    """
    🔎 Lấy chi tiết 1 địa điểm theo ID
    """
    try:
        place = await repository.get_by_id(place_id)
        
        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Place with ID {place_id} not found"
            )
        
        return {
            "success": True,
            "data": place.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get place by ID failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{place_id}", response_model=PlaceResponse)
async def update_place(
    place_id: int,
    place_data: CreatePlaceRequest = Body(...),
    repository: IPlaceRepository = Depends(get_place_repository)
):
    """
    ✏️ Cập nhật thông tin địa điểm
    """
    try:
        # Kiểm tra place tồn tại
        existing_place = await repository.get_by_id(place_id)
        if not existing_place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Place with ID {place_id} not found"
            )
        
        # Convert request sang PlaceLite
        place_lite = PlaceLite(
            id=place_id,  # Giữ nguyên ID
            name=place_data.name,
            priceVnd=place_data.priceVnd,
            summary=place_data.summary,
            description=place_data.description,
            openTime=place_data.openTime,
            closeTime=place_data.closeTime,
            phone=place_data.phone,
            rating=place_data.rating,
            reviewCount=place_data.reviewCount or 0,
            popularity=place_data.popularity or 0,
            imageName=place_data.imageName,
            address=Address(
                houseNumber=place_data.address.houseNumber,
                street=place_data.address.street,
                ward=place_data.address.ward,
                district=place_data.address.district,
                city=place_data.address.city,
                lat=place_data.address.lat,
                lng=place_data.address.lng,
                url=place_data.address.url
            )
        )
        
        # Update
        success = await repository.update(place_lite)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update place"
            )
        
        logger.info(f"✅ Updated place ID {place_id}")
        
        return PlaceResponse(
            success=True,
            message=f"Place ID {place_id} updated successfully",
            data={"id": place_id, "name": place_data.name}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{place_id}", response_model=PlaceResponse)
async def delete_place(
    place_id: int,
    repository: IPlaceRepository = Depends(get_place_repository)
):
    """
    🗑️ Xóa địa điểm theo ID
    """
    try:
        success = await repository.delete_by_id(place_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Place with ID {place_id} not found"
            )
        
        logger.info(f"✅ Deleted place ID {place_id}")
        
        return PlaceResponse(
            success=True,
            message=f"Place ID {place_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats/summary", response_model=dict)
async def get_stats(
    repository: IPlaceRepository = Depends(get_place_repository)
):
    """
    📊 Lấy thống kê tổng quan về database
    """
    try:
        all_places = await repository.get_all()
        total = len(all_places)
        
        # Thống kê theo thành phố
        city_stats = {}
        total_rating = 0
        rated_count = 0
        
        for place in all_places:
            city = place.address.city if place.address else "Unknown"
            city_stats[city] = city_stats.get(city, 0) + 1
            
            if place.rating:
                total_rating += place.rating
                rated_count += 1
        
        avg_rating = total_rating / rated_count if rated_count > 0 else 0
        
        return {
            "success": True,
            "total_places": total,
            "average_rating": round(avg_rating, 2),
            "cities": city_stats,
            "top_cities": sorted(
                city_stats.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
        
    except Exception as e:
        logger.error(f"❌ Get stats failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )