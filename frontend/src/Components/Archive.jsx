const Archive = ({ id, title, artist, image }) => {
    return (

        <a href={`/sales/${id}`} className="container mx-auto flex flex-col p-4 justify-center align-center font-courier border border-gray-100">
            <div className="flex flex-col justify-center items-center mb-4">
                <span className="text-white text-xl sm:text-2xl">
                    {title}
                </span>
                <span>X</span>
                <span>{artist}</span>
            </div>
            <div className="w-full">
                <img className="w-full h-auto max-h-52 object-cover" src={image} alt={title} />
            </div>
        </a>
    )
}

export default Archive