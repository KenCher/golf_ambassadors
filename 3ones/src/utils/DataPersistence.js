/**
 * Data Persistence Utility
 * Handles saving and loading tournament data
 */
export class DataPersistence {
  /**
   * Save tournament data to JSON file
   * @param {Tournament} tournament - Tournament object
   * @param {string} filename - Output filename
   * @returns {Promise<void>}
   */
  static async saveTournament(tournament, filename = 'tournament-data.json') {
    const data = {
      version: '1.0',
      savedAt: new Date().toISOString(),
      tournament: tournament.toJSON()
    };

    if (typeof window !== 'undefined') {
      // Browser environment - use localStorage
      localStorage.setItem(filename, JSON.stringify(data, null, 2));
      return Promise.resolve();
    } else {
      // Node.js environment - use fs
      const fs = await import('fs');
      return fs.promises.writeFile(filename, JSON.stringify(data, null, 2));
    }
  }

  /**
   * Load tournament data from JSON file
   * @param {string} filename - Input filename
   * @returns {Promise<Object>} Tournament data
   */
  static async loadTournament(filename = 'tournament-data.json') {
    if (typeof window !== 'undefined') {
      // Browser environment - use localStorage
      const data = localStorage.getItem(filename);
      if (!data) {
        throw new Error('No saved tournament found');
      }
      return JSON.parse(data);
    } else {
      // Node.js environment - use fs
      const fs = await import('fs');
      const data = await fs.promises.readFile(filename, 'utf-8');
      return JSON.parse(data);
    }
  }

  /**
   * Export tournament to CSV format
   * @param {Tournament} tournament - Tournament object
   * @param {boolean} useNet - Use net scores
   * @returns {string} CSV string
   */
  static exportToCSV(tournament, useNet = false) {
    const leaderboard = tournament.getLeaderboard(useNet);
    
    let csv = 'Position,Player,Handicap Index,Playing Handicap,Gross Score,Net Score,Holes Completed,Status\n';
    
    leaderboard.forEach(entry => {
      csv += `${entry.rank},`;
      csv += `"${entry.name}",`;
      csv += `${entry.handicapIndex},`;
      csv += `${entry.playingHandicap},`;
      csv += `${entry.grossScore || 0},`;
      csv += `${entry.netScore || 0},`;
      csv += `${entry.holesCompleted},`;
      csv += `${entry.isComplete ? 'Complete' : 'In Progress'}\n`;
    });

    return csv;
  }

  /**
   * Export detailed scorecard to CSV
   * @param {Tournament} tournament - Tournament object
   * @returns {string} CSV string
   */
  static exportDetailedScorecard(tournament) {
    const players = tournament.getAllPlayers();
    const course = tournament.course;
    
    // Header row
    let csv = 'Player,Handicap,';
    for (let i = 1; i <= 18; i++) {
      csv += `Hole ${i},`;
    }
    csv += 'Total,Net Total\n';

    // Par row
    csv += 'Par,-,';
    course.holes.forEach(hole => {
      csv += `${hole.par},`;
    });
    csv += `${course.getTotalPar()},-\n`;

    // Player rows
    players.forEach(player => {
      csv += `"${player.name}",${player.playingHandicap},`;
      for (let i = 1; i <= 18; i++) {
        const score = player.getHoleScore(i);
        csv += `${score || '-'},`;
      }
      csv += `${player.totalStrokes || '-'},${player.netScore || '-'}\n`;
    });

    return csv;
  }

  /**
   * Export skins results to CSV
   * @param {Object} skinsResults - Results from SkinsCalculator
   * @returns {string} CSV string
   */
  static exportSkinsToCSV(skinsResults) {
    let csv = 'Hole,Winner,Score,Value,Status\n';
    
    skinsResults.skins.forEach(skin => {
      csv += `${skin.hole},`;
      csv += `"${skin.winner || 'Tied'}",`;
      csv += `${skin.score || '-'},`;
      csv += `${skin.value},`;
      csv += `${skin.carryover ? 'Carryover' : skin.winner ? 'Won' : 'No Score'}\n`;
    });

    csv += '\nPlayer Summary\n';
    csv += 'Player,Skins Won,Holes,Total Value\n';
    
    Object.entries(skinsResults.playerSkins).forEach(([playerId, data]) => {
      if (data.count > 0) {
        csv += `"${data.name}",${data.count},"${data.holes.join(', ')}",${data.value}\n`;
      }
    });

    return csv;
  }

  /**
   * Download data as file (browser only)
   * @param {string} content - File content
   * @param {string} filename - Filename
   * @param {string} mimeType - MIME type
   */
  static downloadFile(content, filename, mimeType = 'text/plain') {
    if (typeof window === 'undefined') {
      throw new Error('Download is only available in browser environment');
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  /**
   * Auto-save tournament data (browser only)
   * @param {Tournament} tournament - Tournament object
   * @param {number} intervalMs - Auto-save interval in milliseconds
   * @returns {number} Interval ID
   */
  static startAutoSave(tournament, intervalMs = 60000) {
    if (typeof window === 'undefined') {
      throw new Error('Auto-save is only available in browser environment');
    }

    return setInterval(() => {
      this.saveTournament(tournament, 'autosave-tournament.json')
        .then(() => console.log('Auto-saved at', new Date().toLocaleTimeString()))
        .catch(err => console.error('Auto-save failed:', err));
    }, intervalMs);
  }

  /**
   * Stop auto-save
   * @param {number} intervalId - Interval ID from startAutoSave
   */
  static stopAutoSave(intervalId) {
    clearInterval(intervalId);
  }

  /**
   * Get list of saved tournaments (browser only)
   * @returns {Array<Object>} List of saved tournaments
   */
  static getSavedTournaments() {
    if (typeof window === 'undefined') {
      throw new Error('This method is only available in browser environment');
    }

    const tournaments = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.endsWith('.json')) {
        try {
          const data = JSON.parse(localStorage.getItem(key));
          if (data.tournament) {
            tournaments.push({
              filename: key,
              name: data.tournament.name,
              savedAt: data.savedAt,
              playerCount: data.tournament.players.length,
              status: data.tournament.status
            });
          }
        } catch (e) {
          // Skip invalid entries
        }
      }
    }
    return tournaments;
  }

  /**
   * Delete saved tournament (browser only)
   * @param {string} filename - Filename to delete
   */
  static deleteSavedTournament(filename) {
    if (typeof window === 'undefined') {
      throw new Error('This method is only available in browser environment');
    }
    localStorage.removeItem(filename);
  }

  /**
   * Clear all saved tournaments (browser only)
   */
  static clearAllSavedTournaments() {
    if (typeof window === 'undefined') {
      throw new Error('This method is only available in browser environment');
    }

    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.endsWith('.json')) {
        keys.push(key);
      }
    }
    keys.forEach(key => localStorage.removeItem(key));
  }
}

// Made with Bob
