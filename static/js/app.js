let championsData = {};
let filteredChampions = {};

document.addEventListener('DOMContentLoaded', function () {
    loadChampions();
});

function loadChampions() {
    fetch('/api/champions')
        .then(response => response.json())
        .then(data => {
            championsData = data;
            filteredChampions = championsData;
            updateChampionGrid();
        })
        .catch(error => console.error('Error fetching champions:', error));
}

function updateChampionGrid() {
    const grid = document.getElementById('champion-grid');
    grid.innerHTML = ''; // Clear current grid

    Object.values(filteredChampions).forEach(champion => {
        const img = document.createElement('img');
        img.src = `https://ddragon.leagueoflegends.com/cdn/img/champion/${champion.id}.jpg`;
        img.alt = champion.name;
        img.className = 'champion-image';

        const championDiv = document.createElement('div');
        championDiv.className = 'champion-card';
        championDiv.appendChild(img);
        championDiv.innerHTML += `<h3>${champion.name}</h3>`;

        grid.appendChild(championDiv);
    });
}

function filterChampions() {
    const searchTerm = document.getElementById('champion-search').value.toLowerCase();
    filteredChampions = Object.values(championsData).filter(champion =>
        champion.name.toLowerCase().includes(searchTerm)
    );
    updateChampionGrid();
}

function updateLanguage() {
    const language = document.getElementById('language-select').value;
    fetch(`/api/champions?lang=${language}`)
        .then(response => response.json())
        .then(data => {
            championsData = data;
            filteredChampions = championsData;
            updateChampionGrid();
        })
        .catch(error => console.error('Error updating language:', error));
}
