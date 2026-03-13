import React, { memo } from 'react';
import { Form } from 'react-bootstrap';
import { FaSearch } from 'react-icons/fa';

const SearchInput = memo(({ searchTerm, setSearchTerm, placeholder }) => (
    <div className="search-bar-wrapper">
        <Form.Control
            type="text"
            placeholder={placeholder}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
        />
        <FaSearch className="search-icon" />
    </div>
));

SearchInput.displayName = 'SearchInput';

export default SearchInput;
