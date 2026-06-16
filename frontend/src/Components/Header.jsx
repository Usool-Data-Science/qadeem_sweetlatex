import { Link } from "react-router-dom"

const Header = () => {
    return (
        <div className="bg-inherit backdrop-blur-md border-y-4 border-t-gray-50 mt-0">
            <div className="flex justify-between align-bottom items-center px-5">

                <Link to="/">
                    <img src="/killerLogo.png" alt="Logo" className="h-20 w-auto rounded-full" />
                </Link>
                <Link to="/">
                    <span className="text-white font-arvo pr-6 hover:underline hover:underline-offset-2">Instagram</span>
                </Link>
            </div>
        </div>
    )
}

export default Header