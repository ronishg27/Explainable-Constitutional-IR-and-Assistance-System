
const navItems = ["Home", "About", "How it Works"];

const Navbar = () => {
  return (
    <nav className=" sticky  top-0 "style={{backgroundColor:'rgb(225, 225, 234)',color:'gray-900'}}>
      <div className="   container mx-auto   flex h-16 items-center justify-between px-4">
        <div className=" ">
          <div className=" m-0 flex items-center gap-1.5">
          < div className=" flex h-9 w-9 items-center justify-center rounded-lg gradient-hero">
            <img src="src\assets\balance.png" alt="there was a pic " />
          </div>
          <span className=" flex text-black text-foreground  text-2xl font-semibold p-1 " style={{ fontFamily: 'var(--font-heading)' }}>
           Constitutional Insight
          </span>
        </div>
        </div>
     <ul className=" text-gray-500 flex items-center gap-5.5">
          {navItems.map((item) => (
            <li key={item}>
              <a
                href="#"
                className="text-md font-bold hover:text-gray-900">
              
                {item}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
