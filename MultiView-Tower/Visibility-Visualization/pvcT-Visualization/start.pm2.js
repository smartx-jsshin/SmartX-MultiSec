module.exports = {
    apps: [{
    name: 'mvf-vis',
    script: './server.js',
    instances: 0,
    exec_mode: 'cluster'
    }]
  }