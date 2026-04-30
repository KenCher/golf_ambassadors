// 🔥 Firebase Configuration
// Replace this with your actual Firebase config from Firebase Console

const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "golf-ambassadors.firebaseapp.com",
  databaseURL: "https://golf-ambassadors-default-rtdb.firebaseio.com",
  projectId: "golf-ambassadors",
  storageBucket: "golf-ambassadors.appspot.com",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get a reference to the database service
const database = firebase.database();

// Export for use in other files
window.golfDatabase = database;

// Made with Bob
