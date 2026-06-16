export const getErrorMessage = (error) => {
  return (
    error?.data?.detail ||
    error?.data?.message ||
    error?.data?.error ||
    error?.error ||
    "Something went wrong!"
  );
};
