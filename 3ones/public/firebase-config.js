// 🔥 Firebase Configuration
// Your actual Firebase config

const firebaseConfig = {
  apiKey: "AIzaSyDAg-PMUqJxembdfLugDX_NGVDfHsktYHg",
  authDomain: "golf-ambassadors.firebaseapp.com",
  databaseURL: "https://golf-ambassadors-default-rtdb.firebaseio.com",
  projectId: "golf-ambassadors",
  storageBucket: "golf-ambassadors.firebasestorage.app",
  messagingSenderId: "191082071768",
  appId: "1:191082071768:web:815e488ccb141683f5f9ad"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get a reference to the database service
const database = firebase.database();

// Export for use in other files
window.golfDatabase = database;

// Made with Bob
