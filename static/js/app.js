let mapChart, trendChart, aqiWeeklyChart, radarChart, historyChart;

function getAQIClass(aqi) {
    if (aqi <= 50) return 'aqi-excellent';
    if (aqi <= 100) return 'aqi-good';
    if (aqi <= 150) return 'aqi-light';
    if (aqi <= 200) return 'aqi-moderate';
    if (aqi <= 300) return 'aqi-heavy';
    return 'aqi-severe';
}

function getAQILevelText(aqi) {
    if (aqi <= 50) return '优';
    if (aqi <= 100) return '良';
    if (aqi <= 150) return '轻度污染';
    if (aqi <= 200) return '中度污染';
    if (aqi <= 300) return '重度污染';
    return '严重污染';
}

const pageTitles = {
    'ranking': '全国城市AQI排行',
    'map': '地图热力图分布',
    'history': '历史趋势数据分析'
};

function showPage(pageName, elem) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('d-none'));
    const pageElement = document.getElementById(`page-${pageName}`);
    pageElement.classList.remove('d-none');
    
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(l => l.classList.remove('active'));
    elem.closest('.nav-link').classList.add('active');
    
    const titleElem = document.getElementById('page-title');
    if (titleElem && pageTitles[pageName]) {
        titleElem.textContent = pageTitles[pageName];
    }
    
    setTimeout(() => {
        if (pageName === 'map') {
            initMap();
            loadMapData();
        }
        if (mapChart) mapChart.resize();
        if (trendChart) trendChart.resize();
        if (aqiWeeklyChart) aqiWeeklyChart.resize();
        if (radarChart) radarChart.resize();
        if (historyChart) historyChart.resize();
    }, 100);
}

async function loadProvinces() {
    const response = await fetch('/api/provinces');
    const provinces = await response.json();
    const select = document.getElementById('province-filter');
    provinces.forEach(p => {
        const option = document.createElement('option');
        option.value = p;
        option.textContent = p;
        select.appendChild(option);
    });
}

async function loadCities() {
    const response = await fetch('/api/cities');
    const cities = await response.json();
    const select = document.getElementById('history-city');
    cities.forEach(c => {
        const option = document.createElement('option');
        option.value = c.id;
        option.textContent = c.name;
        select.appendChild(option);
    });
}

async function loadAQIRanking() {
    const province = document.getElementById('province-filter').value;
    const url = province ? `/api/aqi-ranking?province=${encodeURIComponent(province)}` : '/api/aqi-ranking';
    const response = await fetch(url);
    const data = await response.json();
    
    const tbody = document.getElementById('ranking-tbody');
    tbody.innerHTML = '';
    
    let highAlert = false;
    let severeAlert = false;
    
    data.forEach((item, index) => {
        const aqiClass = getAQIClass(item.aqi);
        
        if (item.aqi > 150) highAlert = true;
        if (item.aqi > 200) severeAlert = true;
        
        const row = document.createElement('tr');
        row.className = item.aqi > 150 ? 'table-danger' : '';
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.city_name}</td>
            <td>${item.province}</td>
            <td class="${aqiClass}">${item.aqi}</td>
            <td class="${aqiClass}">${getAQILevelText(item.aqi)}</td>
            <td>${item.pm25}</td>
            <td>${item.pm10}</td>
            <td><button class="btn btn-sm btn-info" onclick="showCityDetail(${item.city_id})">查看详情</button></td>
        `;
        tbody.appendChild(row);
    });
    
    const banner = document.getElementById('alert-banner');
    if (severeAlert) {
        banner.classList.remove('d-none');
    } else {
        banner.classList.add('d-none');
    }
}

async function showCityDetail(cityId) {
    showPage('city-detail');
    
    const [detailResponse, trendsResponse, historyResponse] = await Promise.all([
        fetch(`/api/city/${cityId}/detail`),
        fetch(`/api/city/${cityId}/24h-trends`),
        fetch(`/api/city/${cityId}/history?days=7`)
    ]);
    
    const detail = await detailResponse.json();
    const trends = await trendsResponse.json();
    const history = await historyResponse.json();
    
    document.getElementById('city-name').textContent = `${detail.city_name} - ${detail.province}`;
    
    init24hTrends(trends);
    init7DayAQI(history);
    initRadar(detail);
}

function initMap() {
    if (!mapChart) {
        mapChart = echarts.init(document.getElementById('china-map'));
        window.addEventListener('resize', () => mapChart.resize());
    }
}

function init24hTrends(data) {
    if (!trendChart) {
        trendChart = echarts.init(document.getElementById('trend-chart'));
        window.addEventListener('resize', () => trendChart.resize());
    }
    
    const timestamps = data.map(d => d.timestamp.slice(11, 16));
    const option = {
        tooltip: {trigger: 'axis'},
        legend: {data: ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']},
        xAxis: {type: 'category', data: timestamps},
        yAxis: {type: 'value'},
        series: [
            {name: 'PM2.5', type: 'line', data: data.map(d => d.pm25)},
            {name: 'PM10', type: 'line', data: data.map(d => d.pm10)},
            {name: 'SO2', type: 'line', data: data.map(d => d.so2)},
            {name: 'NO2', type: 'line', data: data.map(d => d.no2)},
            {name: 'CO', type: 'line', data: data.map(d => d.co)},
            {name: 'O3', type: 'line', data: data.map(d => d.o3)}
        ]
    };
    trendChart.setOption(option);
}

function init7DayAQI(data) {
    if (!aqiWeeklyChart) {
        aqiWeeklyChart = echarts.init(document.getElementById('aqi-weekly-chart'));
        window.addEventListener('resize', () => aqiWeeklyChart.resize());
    }
    
    const dailyData = {};
    data.forEach(d => {
        const date = d.timestamp.slice(0, 10);
        if (!dailyData[date]) {
            dailyData[date] = [];
        }
        dailyData[date].push(d.aqi);
    });
    
    const dates = Object.keys(dailyData).sort();
    const avgAqi = dates.map(date => {
        const values = dailyData[date];
        return Math.round(values.reduce((a, b) => a + b, 0) / values.length);
    });
    
    const option = {
        tooltip: {trigger: 'axis'},
        xAxis: {type: 'category', data: dates},
        yAxis: {type: 'value', name: 'AQI'},
        series: [{
            type: 'bar',
            data: avgAqi,
            itemStyle: {
                color: function(params) {
                    const aqi = params.value;
                    if (aqi <= 50) return '#00e400';
                    if (aqi <= 100) return '#ffff00';
                    if (aqi <= 150) return '#ff7e00';
                    if (aqi <= 200) return '#ff0000';
                    if (aqi <= 300) return '#99004c';
                    return '#7e0023';
                }
            }
        }]
    };
    aqiWeeklyChart.setOption(option);
}

function initRadar(data) {
    if (!radarChart) {
        radarChart = echarts.init(document.getElementById('radar-chart'));
        window.addEventListener('resize', () => radarChart.resize());
    }
    
    const option = {
        tooltip: {},
        radar: {
            indicator: [
                {name: 'PM2.5', max: 200},
                {name: 'PM10', max: 300},
                {name: 'SO2', max: 100},
                {name: 'NO2', max: 150},
                {name: 'CO', max: 15},
                {name: 'O3', max: 300}
            ]
        },
        series: [{
            type: 'radar',
            data: [{
                value: [data.pm25, data.pm10, data.so2, data.no2, data.co, data.o3],
                name: '污染物浓度'
            }]
        }]
    };
    radarChart.setOption(option);
}

async function loadMapData() {
    const response = await fetch('/api/aqi-ranking');
    const data = await response.json();
    
    const mapData = data.map(d => ({
        name: d.city_name,
        value: d.aqi
    }));
    
    const option = {
        title: {text: '全国AQI热力图', left: 'center'},
        tooltip: {
            formatter: function(params) {
                if (params.data) {
                    return `${params.name}<br/>AQI: ${params.data.value} - ${getAQILevelText(params.data.value)}`;
                }
                return params.name;
            }
        },
        visualMap: {
            min: 0,
            max: 300,
            text: ['严重污染', '优'],
            realtime: true,
            calculable: true,
            inRange: {
                color: ['#00e400', '#ffff00', '#ff7e00', '#ff0000', '#99004c', '#7e0023']
            }
        },
        series: [{
            type: 'map',
            map: 'china',
            roam: true,
            data: mapData,
            emphasis: {
                itemStyle: {areaColor: '#eee'}
            }
        }]
    };
    mapChart.setOption(option);
}

async function loadHistoryData() {
    const cityId = document.getElementById('history-city').value;
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    if (!cityId || !startDate || !endDate) {
        alert('请选择城市和日期范围');
        return;
    }
    
    const response = await fetch(`/api/city/${cityId}/history?start_date=${startDate}&end_date=${endDate}`);
    const data = await response.json();
    
    if (!historyChart) {
        historyChart = echarts.init(document.getElementById('history-chart'));
        window.addEventListener('resize', () => historyChart.resize());
    }
    
    const timestamps = data.map(d => d.timestamp.slice(0, 16));
    const option = {
        title: {text: '历史AQI数据', left: 'center'},
        tooltip: {trigger: 'axis'},
        legend: {data: ['AQI', 'PM2.5'], top: 30},
        xAxis: {type: 'category', data: timestamps},
        yAxis: [
            {type: 'value', name: 'AQI', position: 'left'},
            {type: 'value', name: 'μg/m³', position: 'right'}
        ],
        series: [
            {name: 'AQI', type: 'line', yAxisIndex: 0, data: data.map(d => d.aqi)},
            {name: 'PM2.5', type: 'line', yAxisIndex: 1, data: data.map(d => d.pm25)}
        ]
    };
    historyChart.setOption(option);
    window.historyData = data;
    window.selectedCityId = cityId;
    window.selectedDates = {start: startDate, end: endDate};
}

async function exportCSV() {
    const cityId = window.selectedCityId || document.getElementById('history-city').value;
    const startDate = window.selectedDates?.start || document.getElementById('start-date').value;
    const endDate = window.selectedDates?.end || document.getElementById('end-date').value;
    
    if (!cityId || !startDate || !endDate) {
        alert('请先查询历史数据');
        return;
    }
    
    window.location.href = `/api/city/${cityId}/export?start_date=${startDate}&end_date=${endDate}`;
}

async function initApp() {
    await loadProvinces();
    await loadCities();
    await loadAQIRanking();
    setInterval(loadAQIRanking, 10000);
}

document.addEventListener('DOMContentLoaded', initApp);
