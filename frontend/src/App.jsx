import React from 'react'
import Navbar from './components/Navbar'
import SearchBar from './components/SearchBar'
import Mainsearchbar from './components/mainsearchbar'
import Resultdisplay from './components/Resultdisplay'  


const App = () => {
  return (
    <div>
      <Navbar />
      <SearchBar />
      <Mainsearchbar />
      <Resultdisplay />
     
    </div>
  )
}

export default App
