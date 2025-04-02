#hotel_compset_analyzer/output/web_dashboard.py
"""
Web dashboard generator for the Hotel CompSet Analyzer.
Creates an interactive HTML dashboard for viewing competitive set data.
"""

import os
import json
from typing import Dict, List, Any, Optional
import logging
import shutil

from data.hotel import Hotel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# JavaScript content for the dashboard
dashboard_js = """
document.addEventListener('DOMContentLoaded', function() {
    // Set subject hotel name
    document.getElementById('subjectHotelName').textContent = hotelData.subject_hotel.name;
    
    // Set analysis date
    document.getElementById('analysisDate').textContent = hotelData.analysis_date;
    
    // Populate subject hotel info
    populateSubjectHotelInfo();
    
    // Populate competitor info
    populateCompetitorInfo();
    
    // Create charts
    createRoomCountChart();
    createAmenitiesChart();
    
    // Populate comparison table
    populateComparisonTable();
});

function populateSubjectHotelInfo() {
    const subject = hotelData.subject_hotel;
    const infoTable = document.getElementById('subjectHotelInfo');
    
    const rows = [
        { label: 'Brand', value: subject.brand_affiliation || 'Independent' },
        { label: 'Chain Scale', value: subject.chain_scale || 'N/A' },
        { label: 'Address', value: `${subject.address}, ${subject.city}, ${subject.state}` },
        { label: 'Room Count', value: subject.room_count || 'N/A' },
        { label: 'Year Built', value: subject.year_built || 'N/A' },
        { label: 'Year Renovated', value: subject.year_renovated || 'N/A' }
    ];
    
    rows.forEach(row => {
        const tr = document.createElement('tr');
        
        const th = document.createElement('th');
        th.textContent = row.label;
        th.scope = 'row';
        
        const td = document.createElement('td');
        td.textContent = row.value;
        
        tr.appendChild(th);
        tr.appendChild(td);
        infoTable.appendChild(tr);
    });
}

function populateCompetitorInfo() {
    const competitors = hotelData.competitor_hotels;
    
    // Set competitor count
    document.getElementById('competitorCount').innerHTML = `
        <h3>${competitors.length}</h3>
        <p>Competitor Hotels</p>
    `;
    
    // Create competitor list
    const competitorList = document.getElementById('competitorList');
    
    competitors.sort((a, b) => (a.distance_from_subject || 0) - (b.distance_from_subject || 0));
    
    competitors.forEach(hotel => {
        const distance = hotel.distance_from_subject !== null ? 
            `${hotel.distance_from_subject.toFixed(2)} miles` : 'N/A';
        
        const div = document.createElement('div');
        div.className = 'mb-2 p-2 border-bottom';
        div.innerHTML = `
            <div class="d-flex justify-content-between">
                <div>
                    <strong>${hotel.name}</strong>
                    <div class="text-muted small">${hotel.brand_affiliation || 'Independent'}</div>
                </div>
                <div class="text-end">
                    <span class="badge bg-primary">${distance}</span>
                    <div class="text-muted small">${hotel.room_count || 0} rooms</div>
                </div>
            </div>
        `;
        
        competitorList.appendChild(div);
    });
}

function createRoomCountChart() {
    const ctx = document.getElementById('roomCountChart').getContext('2d');
    
    const subject = hotelData.subject_hotel;
    const competitors = hotelData.competitor_hotels;
    
    const hotelNames = [subject.name].concat(competitors.map(h => h.name));
    const roomCounts = [subject.room_count || 0].concat(competitors.map(h => h.room_count || 0));
    
    const backgroundColors = ['rgba(255, 206, 86, 0.6)'].concat(
        competitors.map(() => 'rgba(54, 162, 235, 0.6)')
    );
    
    const borderColors = ['rgba(255, 206, 86, 1)'].concat(
        competitors.map(() => 'rgba(54, 162, 235, 1)')
    );
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hotelNames,
            datasets: [{
                label: 'Room Count',
                data: roomCounts,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Rooms'
                    }
                }
            }
        }
    });
}

function createAmenitiesChart() {
    const ctx = document.getElementById('amenitiesChart').getContext('2d');
    
    const subject = hotelData.subject_hotel;
    const competitors = hotelData.competitor_hotels;
    
    // Count amenities for each hotel
    function countAmenities(hotel) {
        if (!hotel.amenities) return 0;
        
        let count = 0;
        if (hotel.amenities.restaurants && hotel.amenities.restaurants > 0) count++;
        if (hotel.amenities.pool) count++;
        if (hotel.amenities.fitness_center) count++;
        if (hotel.amenities.spa) count++;
        if (hotel.amenities.business_center) count++;
        if (hotel.amenities.club_lounge) count++;
        
        return count;
    }
    
    const hotelNames = [subject.name].concat(competitors.map(h => h.name));
    const amenityCounts = [countAmenities(subject)].concat(competitors.map(countAmenities));
    
    const backgroundColors = ['rgba(255, 206, 86, 0.6)'].concat(
        competitors.map(() => 'rgba(54, 162, 235, 0.6)')
    );
    
    const borderColors = ['rgba(255, 206, 86, 1)'].concat(
        competitors.map(() => 'rgba(54, 162, 235, 1)')
    );
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hotelNames,
            datasets: [{
                label: 'Amenity Count',
                data: amenityCounts,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 6,
                    title: {
                        display: true,
                        text: 'Number of Key Amenities'
                    }
                }
            }
        }
    });
}

function populateComparisonTable() {
    const subject = hotelData.subject_hotel;
    const competitors = hotelData.competitor_hotels;
    
    const tableBody = document.getElementById('comparisonTableBody');
    
    // Add subject hotel row
    const subjectRow = document.createElement('tr');
    subjectRow.className = 'subject-hotel-row';
    
    let meetingSpace = 'N/A';
    if (subject.meeting_space && subject.meeting_space.total_space_sf) {
        meetingSpace = `${subject.meeting_space.total_space_sf.toLocaleString()} SF`;
    }
    
    subjectRow.innerHTML = `
        <td>${subject.name} (Subject)</td>
        <td>${subject.brand_affiliation || 'Independent'}</td>
        <td>${subject.room_count || 'N/A'}</td>
        <td>${subject.year_built || 'N/A'}</td>
        <td>${meetingSpace}</td>
        <td>0.00 mi</td>
    `;
    
    tableBody.appendChild(subjectRow);
    
    // Add competitor rows
    competitors.sort((a, b) => (a.distance_from_subject || 0) - (b.distance_from_subject || 0));
    
    competitors.forEach(hotel => {
        const row = document.createElement('tr');
        
        let meetingSpace = 'N/A';
        if (hotel.meeting_space && hotel.meeting_space.total_space_sf) {
            meetingSpace = `${hotel.meeting_space.total_space_sf.toLocaleString()} SF`;
        }
        
        const distance = hotel.distance_from_subject !== null ?
            `${hotel.distance_from_subject.toFixed(2)} mi` : 'N/A';
        
        row.innerHTML = `
            <td>${hotel.name}</td>
            <td>${hotel.brand_affiliation || 'Independent'}</td>
            <td>${hotel.room_count || 'N/A'}</td>
            <td>${hotel.year_built || 'N/A'}</td>
            <td>${meetingSpace}</td>
            <td>${distance}</td>
        `;
        
        tableBody.appendChild(row);
    });
}
"""

# JavaScript for comparison page
comparison_js = """
document.addEventListener('DOMContentLoaded', function() {
    // Set subject hotel name
    document.getElementById('subjectHotelName').textContent = hotelData.subject_hotel.name;
    
    // Set analysis date
    document.getElementById('analysisDate').textContent = hotelData.analysis_date;
    
    // Populate all comparison tables
    populateBasicTable();
    populateRoomsTable();
    populateAmenitiesTable();
    populateMeetingsTable();
    populateReviewsTable();
});

function populateBasicTable() {
    const subject = hotelData.subject_hotel;
    const competitors = hotelData.competitor_hotels;
    
    const tableBody = document.getElementById('basicTableBody');
    
    // Add subject hotel row
    const subjectRow = document.createElement('tr');
    subjectRow.className = 'subject-hotel-row';
    
    subjectRow.innerHTML = `
        <td>${subject.name} (Subject)</td>
        <td>${subject.brand_affiliation || 'Independent'}</td>
        <td>${subject.chain_scale || 'N/A'}</td>
        <td>${subject.year_built || 'N/A'}</td>
        <td>${subject.year_renovated || 'N/A'}</td>
        <td>0.00 mi</td>
    `;
    
    tableBody.appendChild(subjectRow);
    
    // Add competitor rows
    competitors.sort((a, b) => (a.distance_from_subject || 0) - (b.distance_from_subject || 0));
    
    competitors.forEach(hotel => {
        const row = document.createElement('tr');
        
        const distance = hotel.distance_from_subject !== null ?
            `${hotel.distance_from_subject.toFixed(2)} mi` : 'N/A';
        
        row.innerHTML = `
            <td>${hotel.name}</td>
            <td>${hotel.brand_affiliation || 'Independent'}</td>
            <td>${hotel.chain_scale || 'N/A'}</td>
            <td>${hotel.year_built || 'N/A'}</td>
            <td>${hotel.year_renovated || 'N/A'}</td>
            <td>${distance}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

function populateRoomsTable() {
    const subject = hotelData.subject_hotel;
    const competitors = hotelData.competitor_hotels;
    
    const tableBody = document.getElementById('roomsTableBody');
    
    // Add subject hotel row
    const subjectRow = document.createElement('tr');
    subjectRow.className = 'subject-hotel-row';
    
    const suitePct = subject.suite_percentage !== null ?
        `${subject.suite_percentage.toFixed(1)}%` : 'N/A';
    
    // Get room types as comma separated list
    let roomTypes = 'N/A';
    if (subject.room_types && subject.room_types.length > 0) {
        roomTypes = subject.room_types.map(rt => rt.room_type).join(', ');
    }
    
    subjectRow.innerHTML = `
        <td>${subject.name} (Subject)</td>
        <td>${subject.room_count || 'N/A'}</td>
        <td>${subject.suite_count || 'N/A'}</td>
        <td>${suitePct}</td>
        <td>${roomTypes}</td>
    `;
    
    tableBody.appendChild(subjectRow);
    
    // Add competitor rows
    competitors.forEach(hotel => {
        const row = document.createElement('tr');
        
        const suitePct = hotel.suite_percentage !== null ?
            `${hotel.suite_percentage.toFixed(1)}%` : 'N/A';
        
        // Get room types as comma separated list
        let roomTypes = 'N/A';
        if (hotel.room_types && hotel.room_types.length > 0) {
            roomTypes = hotel.room_types.map(rt => rt.room_type).join(', ');
        }
        
        row.innerHTML = `
            <td>${hotel.name}</td>
            <td>${hotel.room_count || 'N/A'}</td>
            <td>${hotel.suite_count || 'N/A'}</td>
            <td>${suitePct}</td>
            <td>${roomTypes}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

function populateAmenitiesTable() {
    const subject = hotelData.subject_hotel;
    const competitors = hotelData.competitor_hotels;
    
    const tableBody = document.getElementById('amenitiesTableBody');
    
    // Add subject hotel row
    const subjectRow = document.createElement('tr');
    subjectRow.className = 'subject-hotel-row';
    
    const amenities = subject.amenities || {};
    
    subjectRow.innerHTML = `
        <td>${subject.name} (Subject)</td>
        <td>${amenities.restaurants || 0}</td>
        <td>${amenities.pool || 'No'}</td>
        <td>${amenities.fitness_center ? 'Yes' : 'No'}</td>
        <td>${amenities.spa ? 'Yes' : 'No'}</td>
        <td>${amenities.business_center ? 'Yes' : 'No'}</td>
        <td>${amenities.club_lounge ? 'Yes' : 'No'}</td>
        <td>${amenities.resort_fee ? '$' + amenities.resort_fee : 'None'}</td>
    `;
    
    tableBody.appendChild(subjectRow);
    
    // Add competitor rows
    competitors.forEach(hotel => {
        const row = document.createElement('tr');
        
        const amenities = hotel.amenities || {};
        
        row.innerHTML = `
            <td>${hotel.name}</td>
            <td>${amenities.restaurants || 0}</td>
            <td>${amenities.pool || 'No'}</td>
            <td>${amenities.fitness_center ? 'Yes' : 'No'}</td>
            <td>${amenities.spa ? 'Yes' : 'No'}</td>
            <td>${amenities.business_center ? 'Yes' : 'No'}</td>
            <td>${amenities.club_lounge ? 'Yes' : 'No'}</td>
            <td>${amenities.resort_fee ? '$' + amenities.resort_fee : 'None'}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

function populateMeetingsTable() {
    const subject = hotelData.subject_hotel;
    const competitors = hotelData.competitor_hotels;
    
    const tableBody = document.getElementById('meetingsTableBody');
    
    // Add subject hotel row
    const subjectRow = document.createElement('tr');
    subjectRow.className = 'subject-hotel-row';
    
    const ms = subject.meeting_space || {};
    
    const sfPerKey = ms.meeting_space_per_key !== null ?
        ms.meeting_space_per_key.toFixed(1) : 'N/A';
    
    subjectRow.innerHTML = `
        <td>${subject.name} (Subject)</td>
        <td>${ms.total_space_sf ? ms.total_space_sf.toLocaleString() : 'N/A'}</td>
        <td>${ms.total_rooms || 'N/A'}</td>
        <td>${ms.largest_room_sf ? ms.largest_room_sf.toLocaleString() : 'N/A'}</td>
        <td>${sfPerKey}</td>
    `;
    
    tableBody.appendChild(subjectRow);
    
    // Add competitor rows
    competitors.forEach(hotel => {
        const row = document.createElement('tr');
        
        const ms = hotel.meeting_space || {};
        
        const sfPerKey = ms.meeting_space_per_key !== null ?
            ms.meeting_space_per_key.toFixed(1) : 'N/A';
        
        row.innerHTML = `
            <td>${hotel.name}</td>
            <td>${ms.total_space_sf ? ms.total_space_sf.toLocaleString() : 'N/A'}</td>
            <td>${ms.total_rooms || 'N/A'}</td>
            <td>${ms.largest_room_sf ? ms.largest_room_sf.toLocaleString() : 'N/A'}</td>
            <td>${sfPerKey}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

function populateReviewsTable() {
    const subject = hotelData.subject_hotel;
    const competitors = hotelData.competitor_hotels;
    
    const tableBody = document.getElementById('reviewsTableBody');
    
    // Helper function to get review score by platform
    function getReviewScore(hotel, platform) {
        if (!hotel.reviews) return 'N/A';
        
        const review = hotel.reviews.find(r => 
            r.platform.toLowerCase().includes(platform.toLowerCase())
        );
        
        if (!review) return 'N/A';
        
        return `${review.score.toFixed(1)} (${review.total_reviews})`;
    }
    
    // Helper function to get common themes from all reviews
    function getCommonThemes(hotel) {
        if (!hotel.reviews) return 'N/A';
        
        const themes = [];
        hotel.reviews.forEach(review => {
            if (review.common_themes) {
                themes.push(...review.common_themes);
            }
        });
        
        if (themes.length === 0) return 'N/A';
        
        // Return top 3 themes
        return themes.slice(0, 3).join(', ');
    }
    
    // Add subject hotel row
    const subjectRow = document.createElement('tr');
    subjectRow.className = 'subject-hotel-row';
    
    subjectRow.innerHTML = `
        <td>${subject.name} (Subject)</td>
        <td>${getReviewScore(subject, 'tripadvisor')}</td>
        <td>${getReviewScore(subject, 'google')}</td>
        <td>${getReviewScore(subject, 'booking')}</td>
        <td>${getCommonThemes(subject)}</td>
    `;
    
    tableBody.appendChild(subjectRow);
    
    // Add competitor rows
    competitors.forEach(hotel => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${hotel.name}</td>
            <td>${getReviewScore(hotel, 'tripadvisor')}</td>
            <td>${getReviewScore(hotel, 'google')}</td>
            <td>${getReviewScore(hotel, 'booking')}</td>
            <td>${getCommonThemes(hotel)}</td>
        `;
        
        tableBody.appendChild(row);
    });
}
"""

# JavaScript for details page
details_js = """
document.addEventListener('DOMContentLoaded', function() {
    // Set analysis date
    document.getElementById('analysisDate').textContent = hotelData.analysis_date;
    
    // Populate hotel selector
    populateHotelSelector();
    
    // Show subject hotel details by default
    showHotelDetails(hotelData.subject_hotel);
    
    // Add event listener to hotel selector
    document.getElementById('hotelSelector').addEventListener('change', function(e) {
        const hotelName = e.target.value;
        let selectedHotel = null;
        
        if (hotelData.subject_hotel.name === hotelName) {
            selectedHotel = hotelData.subject_hotel;
        } else {
            selectedHotel = hotelData.competitor_hotels.find(h => h.name === hotelName);
        }
        
        if (selectedHotel) {
            showHotelDetails(selectedHotel);
        }
    });
});

function populateHotelSelector() {
    const selector = document.getElementById('hotelSelector');
    
    // Add subject hotel
    const subjectOption = document.createElement('option');
    subjectOption.value = hotelData.subject_hotel.name;
    subjectOption.textContent = `${hotelData.subject_hotel.name} (Subject)`;
    selector.appendChild(subjectOption);
    
    // Add separator
    const separator = document.createElement('option');
    separator.disabled = true;
    separator.textContent = '─────────────────';
    selector.appendChild(separator);
    
    // Add competitor hotels
    const competitors = [...hotelData.competitor_hotels];
    competitors.sort((a, b) => (a.distance_from_subject || 0) - (b.distance_from_subject || 0));
    
    competitors.forEach(hotel => {
        const option = document.createElement('option');
        option.value = hotel.name;
        
        const distance = hotel.distance_from_subject !== null ?
            `(${hotel.distance_from_subject.toFixed(2)} mi)` : '';
        
        option.textContent = `${hotel.name} ${distance}`;
        selector.appendChild(option);
    });
}

function showHotelDetails(hotel) {
    // Update selected hotel name in header
    document.getElementById('selectedHotelName').textContent = 
        `${hotel.name} ${hotel.is_subject ? '(Subject Hotel)' : ''}`;
    
    // Get details container
    const detailsContainer = document.getElementById('hotelDetails');
    detailsContainer.innerHTML = '';
    
    // Basic Info Section
    const basicSection = document.createElement('div');
    basicSection.className = 'hotel-details-section';
    
    basicSection.innerHTML = `
        <h4>Basic Information</h4>
        <div class="row">
            <div class="col-md-6">
                <p><strong>Brand:</strong> ${hotel.brand_affiliation || 'Independent'}</p>
                <p><strong>Chain Scale:</strong> ${hotel.chain_scale || 'N/A'}</p>
                <p><strong>Address:</strong> ${hotel.address}, ${hotel.city}, ${hotel.state}, ${hotel.country}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Year Built:</strong> ${hotel.year_built || 'N/A'}</p>
                <p><strong>Year Renovated:</strong> ${hotel.year_renovated || 'N/A'}</p>
                ${!hotel.is_subject ? `<p><strong>Distance from Subject:</strong> ${hotel.distance_from_subject ? hotel.distance_from_subject.toFixed(2) + ' miles' : 'N/A'}</p>` : ''}
            </div>
        </div>
    `;
    
    detailsContainer.appendChild(basicSection);
    
    // Rooms Section
    const roomsSection = document.createElement('div');
    roomsSection.className = 'hotel-details-section';
    
    const suitePct = hotel.suite_percentage !== null ?
        `${hotel.suite_percentage.toFixed(1)}%` : 'N/A';
    
    let roomTypesList = '<p>No room type information available</p>';
    
    if (hotel.room_types && hotel.room_types.length > 0) {
        roomTypesList = '<ul>';
        hotel.room_types.forEach(rt => {
            const size = rt.size_sf ? `(${rt.size_sf} ${rt.size_metric || 'SF'})` : '';
            roomTypesList += `<li>${rt.room_type} ${size}</li>`;
        });
        roomTypesList += '</ul>';
    }
    
    roomsSection.innerHTML = `
        <h4>Rooms</h4>
        <div class="row">
            <div class="col-md-6">
                <p><strong>Room Count:</strong> ${hotel.room_count || 'N/A'}</p>
                <p><strong>Suite Count:</strong> ${hotel.suite_count || 'N/A'}</p>
                <p><strong>Suite Percentage:</strong> ${suitePct}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Room Types:</strong></p>
                ${roomTypesList}
            </div>
        </div>
    `;
    
    detailsContainer.appendChild(roomsSection);
    
    // Amenities Section
    const amenitiesSection = document.createElement('div');
    amenitiesSection.className = 'hotel-details-section';
    
    const amenities = hotel.amenities || {};
    
    // Restaurant list
    let restaurantList = '<p>No restaurant information available</p>';
    
    if (amenities.restaurants && amenities.restaurants.length > 0) {
        restaurantList = '<ul>';
        
        // Check if restaurants is an array of objects or strings
        if (typeof amenities.restaurants[0] === 'object') {
            amenities.restaurants.forEach(r => {
                restaurantList += `<li>${r.name || 'Unnamed'} ${r.type ? `(${r.type})` : ''}</li>`;
            });
        } else {
            amenities.restaurants.forEach(r => {
                restaurantList += `<li>${r}</li>`;
            });
        }
        
        restaurantList += '</ul>';
    }
    
    // Bars/lounges list
    let barsList = '<p>No bar/lounge information available</p>';
    
    if (amenities.bars_lounges && amenities.bars_lounges.length > 0) {
        barsList = '<ul>';
        amenities.bars_lounges.forEach(b => {
            barsList += `<li>${b}</li>`;
        });
        barsList += '</ul>';
    }
    
    // Other amenities list
    let otherList = '';
    
    if (amenities.other_amenities && amenities.other_amenities.length > 0) {
        otherList = '<p><strong>Other Amenities:</strong></p><ul>';
        amenities.other_amenities.forEach(a => {
            otherList += `<li>${a}</li>`;
        });
        otherList += '</ul>';
    }
    
    amenitiesSection.innerHTML = `
        <h4>Amenities</h4>
        <div class="row">
            <div class="col-md-6">
                <p><strong>Restaurants:</strong></p>
                ${restaurantList}
                
                <p><strong>Bars/Lounges:</strong></p>
                ${barsList}
            </div>
            <div class="col-md-6">
                <p><strong>Pool:</strong> ${amenities.pool || 'No'}</p>
                <p><strong>Fitness Center:</strong> ${amenities.fitness_center ? 'Yes' : 'No'}</p>
                <p><strong>Spa:</strong> ${amenities.spa ? 'Yes' : 'No'}</p>
                <p><strong>Business Center:</strong> ${amenities.business_center ? 'Yes' : 'No'}</p>
                <p><strong>Club Lounge:</strong> ${amenities.club_lounge ? 'Yes' : 'No'}</p>
                <p><strong>Parking:</strong> ${amenities.parking_details || 'N/A'}</p>
                <p><strong>Parking Cost:</strong> ${amenities.parking_cost ? '$' + amenities.parking_cost : 'N/A'}</p>
                <p><strong>Resort Fee:</strong> ${amenities.resort_fee ? '$' + amenities.resort_fee : 'None'}</p>
                ${otherList}
            </div>
        </div>
    `;
    
    detailsContainer.appendChild(amenitiesSection);
    
    // Meeting Space Section
    const meetingSection = document.createElement('div');
    meetingSection.className = 'hotel-details-section';
    
    const ms = hotel.meeting_space || {};
    
    meetingSection.innerHTML = `
        <h4>Meeting Space</h4>
        <div class="row">
            <div class="col-md-6">
                <p><strong>Total Space:</strong> ${ms.total_space_sf ? ms.total_space_sf.toLocaleString() + ' SF' : 'N/A'}</p>
                <p><strong>Number of Meeting Rooms:</strong> ${ms.total_rooms || 'N/A'}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Largest Room:</strong> ${ms.largest_room_sf ? ms.largest_room_sf.toLocaleString() + ' SF' : 'N/A'}</p>
                <p><strong>SF per Key:</strong> ${ms.meeting_space_per_key ? ms.meeting_space_per_key.toFixed(1) : 'N/A'}</p>
            </div>
        </div>
    `;
    
    detailsContainer.appendChild(meetingSection);
    
    // Reviews Section
    const reviewsSection = document.createElement('div');
    reviewsSection.className = 'hotel-details-section';
    
    let reviewsContent = '<p>No review information available</p>';
    
    if (hotel.reviews && hotel.reviews.length > 0) {
        reviewsContent = '';
        
        hotel.reviews.forEach(review => {
            let themesContent = '';
            
            if (review.common_themes && review.common_themes.length > 0) {
                themesContent = '<p><strong>Common Themes:</strong></p><ul>';
                review.common_themes.forEach(theme => {
                    themesContent += `<li>${theme}</li>`;
                });
                themesContent += '</ul>';
            }
            
            reviewsContent += `
                <div class="mb-3">
                    <h5>${review.platform}</h5>
                    <p><strong>Score:</strong> ${review.score.toFixed(1)} / 5.0</p>
                    <p><strong>Total Reviews:</strong> ${review.total_reviews}</p>
                    ${themesContent}
                </div>
            `;
        });
    }
    
    reviewsSection.innerHTML = `
        <h4>Reviews</h4>
        ${reviewsContent}
    `;
    
    detailsContainer.appendChild(reviewsSection);
}
"""

# CSS styles definition
styles_css = """
body {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.footer {
    margin-top: auto;
}

.dashboard-title {
    color: #0d6efd;
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 10px;
}

.subject-hotel-row {
    background-color: rgba(255, 255, 0, 0.2) !important;
    font-weight: bold;
}

.card {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.hotel-details-section {
    margin-bottom: 20px;
}

.hotel-details-section h4 {
    color: #0d6efd;
    border-bottom: 1px solid #e9ecef;
    padding-bottom: 5px;
    margin-bottom: 10px;
}

.table-responsive {
    overflow-x: auto;
}
"""


def create_dashboard(subject_hotel: Hotel, competitor_hotels: List[Hotel], 
                    output_dir: str) -> str:
    """
    Create a web dashboard for the competitive set analysis.
    
    Args:
        subject_hotel: Subject hotel
        competitor_hotels: List of competitor hotels
        output_dir: Directory to save the dashboard files
        
    Returns:
        Path to the dashboard directory
    """
    try:
        # Create dashboard directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create data.js file with hotel data
        create_data_js(subject_hotel, competitor_hotels, output_dir)
        
        # Create HTML, CSS, and JS files
        create_html_files(subject_hotel, output_dir)
        
        # Create map
        from output.map_generator import MapGenerator
        map_generator = MapGenerator()
        map_file = map_generator.create_map(
            subject_hotel, 
            competitor_hotels,
            os.path.join(output_dir, "map.html")
        )
        
        logger.info(f"Web dashboard created at: {output_dir}")
        return output_dir
        
    except Exception as e:
        logger.error(f"Error creating web dashboard: {e}")
        return ""


def create_data_js(subject_hotel: Hotel, competitor_hotels: List[Hotel], output_dir: str):
    """
    Create data.js file with hotel data.
    
    Args:
        subject_hotel: Subject hotel
        competitor_hotels: List of competitor hotels
        output_dir: Output directory
    """
    # Convert hotel objects to dictionaries
    def hotel_to_dict(hotel):
        """Convert a Hotel object to a dictionary suitable for JSON."""
        hotel_dict = {
            "name": hotel.name,
            "is_subject": hotel.is_subject,
            "address": hotel.address,
            "city": hotel.city,
            "state": hotel.state,
            "country": hotel.country,
            "brand_affiliation": hotel.brand_affiliation,
            "chain_scale": hotel.chain_scale,
            "year_built": hotel.year_built,
            "year_renovated": hotel.year_renovated,
            "room_count": hotel.room_count,
            "suite_count": hotel.suite_count,
            "suite_percentage": hotel.suite_percentage,
            "latitude": hotel.latitude,
            "longitude": hotel.longitude,
            "distance_from_subject": hotel.distance_from_subject
        }
        
        # Add amenities if available
        if hotel.amenities:
            hotel_dict["amenities"] = {
                "restaurants": len(hotel.amenities.restaurants) if hotel.amenities.restaurants else 0,
                "bars_lounges": len(hotel.amenities.bars_lounges) if hotel.amenities.bars_lounges else 0,
                "pool": hotel.amenities.pool,
                "fitness_center": hotel.amenities.fitness_center,
                "spa": hotel.amenities.spa,
                "business_center": hotel.amenities.business_center,
                "club_lounge": hotel.amenities.club_lounge,
                "resort_fee": hotel.amenities.resort_fee
            }
        
        # Add meeting space if available
        if hotel.meeting_space:
            hotel_dict["meeting_space"] = {
                "total_space_sf": hotel.meeting_space.total_space_sf,
                "total_rooms": hotel.meeting_space.total_rooms,
                "largest_room_sf": hotel.meeting_space.largest_room_sf,
                "meeting_space_per_key": hotel.meeting_space.meeting_space_per_key
            }
        
        # Add reviews if available
        if hotel.reviews:
            hotel_dict["reviews"] = []
            for review in hotel.reviews:
                hotel_dict["reviews"].append({
                    "platform": review.platform,
                    "score": review.score,
                    "total_reviews": review.total_reviews,
                    "common_themes": review.common_themes
                })
        
        return hotel_dict
    
    # Convert hotels to dictionaries
    subject_dict = hotel_to_dict(subject_hotel)
    competitor_dicts = [hotel_to_dict(hotel) for hotel in competitor_hotels]
    
    # Create data object
    data_obj = {
        "subject_hotel": subject_dict,
        "competitor_hotels": competitor_dicts,
        "analysis_date": "",  # Add current date in JS
    }
    
    # Write data.js file
    with open(os.path.join(output_dir, "data.js"), "w", encoding="utf-8") as f:
        f.write("const hotelData = ")
        json.dump(data_obj, f, indent=2)
        f.write(";\n")
        f.write("hotelData.analysis_date = new Date().toISOString().split('T')[0];")


def create_html_files(subject_hotel: Hotel, output_dir: str):
    """
    Create HTML, CSS, and JS files for the dashboard.
    
    Args:
        subject_hotel: Subject hotel for title
        output_dir: Output directory
    """
    # Create index.html
    index_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CompSet Analysis: {subject_hotel.name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Hotel CompSet Analyzer</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link active" href="index.html">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="map.html">Map</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="comparison.html">Comparison</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="details.html">Details</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="dashboard-title">CompSet Analysis: <span id="subjectHotelName"></span></h1>
                <p class="text-muted">Analysis Date: <span id="analysisDate"></span></p>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Subject Hotel Overview</h5>
                    </div>
                    <div class="card-body">
                        <table class="table table-striped">
                            <tbody id="subjectHotelInfo">
                                <!-- Populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Competitive Set</h5>
                    </div>
                    <div class="card-body">
                        <div id="competitorCount" class="text-center mb-3">
                            <!-- Populated by JavaScript -->
                        </div>
                        <div id="competitorList">
                            <!-- Populated by JavaScript -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Room Count Comparison</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="roomCountChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Amenities Comparison</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="amenitiesChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Hotel Comparison Summary</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Hotel</th>
                                        <th>Brand</th>
                                        <th>Rooms</th>
                                        <th>Year Built</th>
                                        <th>Meeting Space</th>
                                        <th>Distance</th>
                                    </tr>
                                </thead>
                                <tbody id="comparisonTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="footer mt-4 py-3 bg-light">
        <div class="container text-center">
            <span class="text-muted">Hotel CompSet Analyzer Dashboard</span>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script src="data.js"></script>
    <script src="dashboard.js"></script>
</body>
</html>
    """
    
    # Create comparison.html
    comparison_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CompSet Comparison: {subject_hotel.name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Hotel CompSet Analyzer</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="index.html">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="map.html">Map</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="comparison.html">Comparison</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="details.html">Details</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="dashboard-title">CompSet Comparison: <span id="subjectHotelName"></span></h1>
                <p class="text-muted">Analysis Date: <span id="analysisDate"></span></p>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <ul class="nav nav-tabs" id="comparisonTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="basic-tab" data-bs-toggle="tab" data-bs-target="#basic" type="button" role="tab">Basic Info</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="rooms-tab" data-bs-toggle="tab" data-bs-target="#rooms" type="button" role="tab">Rooms</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="amenities-tab" data-bs-toggle="tab" data-bs-target="#amenities" type="button" role="tab">Amenities</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="meetings-tab" data-bs-toggle="tab" data-bs-target="#meetings" type="button" role="tab">Meeting Space</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="reviews-tab" data-bs-toggle="tab" data-bs-target="#reviews" type="button" role="tab">Reviews</button>
                    </li>
                </ul>
                
                <div class="tab-content" id="comparisonTabContent">
                    <div class="tab-pane fade show active" id="basic" role="tabpanel">
                        <div class="table-responsive mt-3">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Hotel</th>
                                        <th>Brand</th>
                                        <th>Chain Scale</th>
                                        <th>Year Built</th>
                                        <th>Year Renovated</th>
                                        <th>Distance (mi)</th>
                                    </tr>
                                </thead>
                                <tbody id="basicTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane fade" id="rooms" role="tabpanel">
                        <div class="table-responsive mt-3">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Hotel</th>
                                        <th>Room Count</th>
                                        <th>Suite Count</th>
                                        <th>Suite %</th>
                                        <th>Room Types</th>
                                    </tr>
                                </thead>
                                <tbody id="roomsTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane fade" id="amenities" role="tabpanel">
                        <div class="table-responsive mt-3">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Hotel</th>
                                        <th>Restaurants</th>
                                        <th>Pool</th>
                                        <th>Fitness Center</th>
                                        <th>Spa</th>
                                        <th>Business Center</th>
                                        <th>Club Lounge</th>
                                        <th>Resort Fee</th>
                                    </tr>
                                </thead>
                                <tbody id="amenitiesTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane fade" id="meetings" role="tabpanel">
                        <div class="table-responsive mt-3">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Hotel</th>
                                        <th>Total Space (SF)</th>
                                        <th># of Rooms</th>
                                        <th>Largest Room (SF)</th>
                                        <th>SF per Key</th>
                                    </tr>
                                </thead>
                                <tbody id="meetingsTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="tab-pane fade" id="reviews" role="tabpanel">
                        <div class="table-responsive mt-3">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Hotel</th>
                                        <th>TripAdvisor</th>
                                        <th>Google</th>
                                        <th>Booking.com</th>
                                        <th>Common Themes</th>
                                    </tr>
                                </thead>
                                <tbody id="reviewsTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="footer mt-4 py-3 bg-light">
        <div class="container text-center">
            <span class="text-muted">Hotel CompSet Analyzer Dashboard</span>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="data.js"></script>
    <script src="comparison.js"></script>
</body>
</html>
    """
    
    # Create details.html
    details_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hotel Details: {subject_hotel.name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Hotel CompSet Analyzer</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="index.html">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="map.html">Map</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="comparison.html">Comparison</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="details.html">Details</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="dashboard-title">Hotel Details</h1>
                <p class="text-muted">Analysis Date: <span id="analysisDate"></span></p>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-3">
                <div class="card">
                    <div class="card-header">
                        <h5>Select Hotel</h5>
                    </div>
                    <div class="card-body">
                        <select id="hotelSelector" class="form-select">
                            <!-- Populated by JavaScript -->
                        </select>
                    </div>
                </div>
            </div>
            <div class="col-md-9">
                <div class="card">
                    <div class="card-header">
                        <h5 id="selectedHotelName">Hotel Details</h5>
                    </div>
                    <div class="card-body">
                        <div id="hotelDetails">
                            <!-- Populated by JavaScript -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="footer mt-4 py-3 bg-light">
        <div class="container text-center">
            <span class="text-muted">Hotel CompSet Analyzer Dashboard</span>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="data.js"></script>
    <script src="details.js"></script>
</body>
</html>
    """
    
    # Write files
    with open(os.path.join(output_dir, "dashboard.js"), "w", encoding="utf-8") as f:
        f.write(dashboard_js)
    
    with open(os.path.join(output_dir, "comparison.js"), "w", encoding="utf-8") as f:
        f.write(comparison_js)
    
    with open(os.path.join(output_dir, "details.js"), "w", encoding="utf-8") as f:
        f.write(details_js)
    
    with open(os.path.join(output_dir, "styles.css"), "w", encoding="utf-8") as f:
        f.write(styles_css)
    
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    
    with open(os.path.join(output_dir, "comparison.html"), "w", encoding="utf-8") as f:
        f.write(comparison_html)
    
    with open(os.path.join(output_dir, "details.html"), "w", encoding="utf-8") as f:
        f.write(details_html)