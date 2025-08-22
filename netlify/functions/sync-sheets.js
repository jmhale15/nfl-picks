const { exec } = require('child_process');

exports.handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  return new Promise((resolve) => {
    // Change to the root directory and run the sync script
    const command = 'cd /opt/build/repo && python3 sync-to-sheets.py';
    
    exec(command, { timeout: 60000 }, (error, stdout, stderr) => {
      if (error) {
        resolve({
          statusCode: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
          body: JSON.stringify({
            success: false,
            error: error.message,
            stderr: stderr
          })
        });
      } else {
        resolve({
          statusCode: 200,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
          body: JSON.stringify({
            success: true,
            output: stdout,
            message: 'Google Sheets sync completed successfully'
          })
        });
      }
    });
  });
};