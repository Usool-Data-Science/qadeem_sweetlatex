const ProgressBar = ({ daysLeft, deadLine }) => {
    const progressWidth = (deadLine - daysLeft) / deadLine * 100;
    return (

        <div style={{ height: '2px' }} className="bg-red-600 w-full my-2 mr-2"
        >
            <div className="relative bg-white inset-0 border-black" style={{
                width: `${progressWidth}%`,
                height: '2px'
            }}>
            </div>
        </div>
    )
}

export default ProgressBar