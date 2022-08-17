import json
import re
import urllib.parse
from typing import List, Optional

import aiohttp

_search_data = re.compile('(?<=RELAY_STORE__ = )(.*)(?=};)')


async def search_teacher(name: str) -> Optional[List[dict]]:
    teachers: List[dict] = []

    # Get page data
    async with aiohttp.ClientSession() as session:
        result = await session.get(url=f"https://www.ratemyprofessors.com/search/teachers?query={urllib.parse.quote(name)}")
        page_data: list = _search_data.findall(await result.text())

    # If invalid
    if len(page_data) < 1:
        return None

    # Payload
    payload: dict = json.loads(page_data[0] + "}")
    for key, value in payload.items():
        # Iterate through teachers
        if not value.get("__typename") == "Teacher":
            continue

        # Get school reference
        __school_id = value.get('school', {}).get("__ref")

        # Add to teacher list
        teachers.append({
            "id": value.get("legacyId"),
            "rating": value.get("avgRating"),
            "ratings": value.get("numRatings"),
            "first_name": value.get("firstName"),
            "last_name": value.get("lastName"),
            "department": value.get("department"),
            "difficulty": value.get("avgDifficulty"),
            "would_take_again_percent": value.get("wouldTakeAgainPercent"),
            "school": payload.get(__school_id, {}).get("name") if payload.get(__school_id) else None
        })

    return teachers


async def get_teacher_info(legacy_id: int):
    teacher: dict = dict()

    async with aiohttp.ClientSession() as session:
        result = await session.get(f"https://www.ratemyprofessors.com/ShowRatings.jsp?tid={legacy_id}")
        page_data: list = _search_data.findall(await result.text())

    # If invalid
    if len(page_data) < 1:
        return None

    # Payload
    payload: dict = json.loads(page_data[0] + "}")

    for key, value in payload.items():
        # Iterate through teachers (there will only ever be one)
        if not value.get("__typename") == "Teacher":
            continue

        teacher = value

        __school_id = value.get('school', dict()).get("__ref")
        __rating_distribution = value.get("ratingsDistribution", dict()).get("__ref")

        teacher["school"] = payload.get(__school_id)
        teacher["ratingsDistribution"] = payload.get(__rating_distribution)
        teacher["courses"] = []

        # Get course list
        for code in value.get("courseCodes", {}).get("__refs", []):
            course_data: dict = payload.get(code, dict())

            teacher["courses"].append({
                "course": course_data.get("courseName"),
                "ratings": course_data.get("courseCount")
            })

        # Get ratings
        __rating_ref = value.get("ratings(first:20)", dict()).get("__ref", dict())
        __rating_list = payload.get(__rating_ref, dict()).get("edges", dict()).get("__refs", []) if __rating_ref else []
        teacher["ratings"] = []

        for code in __rating_list:
            __rating_ref: dict = payload.get(code, dict()).get("node", dict()).get("__ref", None)
            if not __rating_ref:
                continue

            rating = payload.get(__rating_ref)
            teacher["ratings"].append(
                rating
            )

    return teacher


